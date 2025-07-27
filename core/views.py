"""
Views for JuridiskPorten core functionality
Secure views with package-based access control
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    TemplateView, ListView, DetailView, CreateView, UpdateView
)
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, HttpResponseForbidden, FileResponse
from django.utils import timezone
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
import logging

from .models import User, LegalPackage, PackageSubscription, Content, UserActivity
from .forms import CustomUserCreationForm, UserProfileForm

logger = logging.getLogger(__name__)


class CustomLoginView(LoginView):
    """
    Custom login view with activity tracking
    """
    template_name = 'core/auth/login.html'
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        """Log successful login"""
        response = super().form_valid(form)
        
        # Log login activity
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='login',
            description='User logged in',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(self.request, f'Welcome back, {self.request.user.get_full_name()}!')
        return response
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class CustomLogoutView(LogoutView):
    """
    Custom logout view with activity tracking
    """
    template_name = 'core/auth/logout.html'
    
    def dispatch(self, request, *args, **kwargs):
        """Log logout activity before logging out"""
        if request.user.is_authenticated:
            UserActivity.objects.create(
                user=request.user,
                activity_type='logout',
                description='User logged out',
                ip_address=self.get_client_ip(),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        return super().dispatch(request, *args, **kwargs)
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class RegisterView(CreateView):
    """
    User registration view
    """
    model = User
    form_class = CustomUserCreationForm
    template_name = 'core/auth/register.html'
    success_url = reverse_lazy('core:login')
    
    def form_valid(self, form):
        """Process successful registration"""
        response = super().form_valid(form)
        
        # Log registration
        logger.info(f"New user registered: {self.object.email}")
        
        messages.success(
            self.request, 
            'Registration successful! You can now log in.'
        )
        return response


class PasswordResetView(TemplateView):
    """
    Password reset view (placeholder for now)
    """
    template_name = 'core/auth/password_reset.html'


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    User dashboard showing available packages and content
    """
    template_name = 'core/dashboard.html'
    login_url = reverse_lazy('core:login')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's active packages
        active_packages = self.request.user.get_active_packages()
        
        # Get available packages
        all_packages = LegalPackage.objects.filter(is_active=True).order_by('sort_order')
        
        # Get recent content from user's packages
        user_package_ids = [sub.package.id for sub in active_packages]
        recent_content = Content.objects.filter(
            package_id__in=user_package_ids,
            status='published'
        ).select_related('package', 'category').order_by('-published_at')[:5]
        
        context.update({
            'active_packages': active_packages,
            'all_packages': all_packages,
            'recent_content': recent_content,
            'user_package_count': len(active_packages),
        })
        
        return context


class ProfileView(LoginRequiredMixin, UpdateView):
    """
    User profile management view
    """
    model = User
    form_class = UserProfileForm
    template_name = 'core/profile.html'
    success_url = reverse_lazy('core:profile')
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        """Process profile update"""
        response = super().form_valid(form)
        
        # Log profile update
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='profile_update',
            description='Profile updated',
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(self.request, 'Profile updated successfully!')
        return response
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class PackageListView(ListView):
    """
    List all available legal packages
    """
    model = LegalPackage
    template_name = 'core/packages/list.html'
    context_object_name = 'packages'
    queryset = LegalPackage.objects.filter(is_active=True).order_by('sort_order')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add user's current subscriptions if authenticated
        if self.request.user.is_authenticated:
            user_packages = self.request.user.get_active_packages()
            context['user_package_types'] = [
                sub.package.package_type for sub in user_packages
            ]
        
        return context


class PackageDetailView(DetailView):
    """
    Detailed view of a specific legal package
    """
    model = LegalPackage
    template_name = 'core/packages/detail.html'
    context_object_name = 'package'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Check if user has access to this package
        has_access = False
        subscription = None
        
        if self.request.user.is_authenticated:
            try:
                subscription = PackageSubscription.objects.get(
                    user=self.request.user,
                    package=self.object,
                    is_active=True,
                    expires_at__gt=timezone.now()
                )
                has_access = True
            except PackageSubscription.DoesNotExist:
                pass
        
        # Get sample content (always visible)
        sample_content = Content.objects.filter(
            package=self.object,
            status='published',
            featured=True
        ).select_related('category')[:3]
        
        context.update({
            'has_access': has_access,
            'subscription': subscription,
            'sample_content': sample_content,
        })
        
        return context


class ContentDetailView(LoginRequiredMixin, DetailView):
    """
    Detailed view of content with package access control
    """
    model = Content
    template_name = 'core/content/detail.html'
    context_object_name = 'content'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Content.objects.filter(status='published').select_related(
            'package', 'category', 'author'
        )
    
    def get_object(self, queryset=None):
        """Get object and check package access"""
        obj = super().get_object(queryset)
        
        # Check if user has access to this content's package
        if not self.has_package_access(obj.package):
            raise PermissionError("No access to this package")
        
        # Increment view count
        obj.view_count += 1
        obj.save(update_fields=['view_count'])
        
        # Log content view
        UserActivity.objects.create(
            user=self.request.user,
            activity_type='content_view',
            description=f'Viewed content: {obj.title}',
            content=obj,
            package=obj.package,
            ip_address=self.get_client_ip(),
            user_agent=self.request.META.get('HTTP_USER_AGENT', '')
        )
        
        return obj
    
    def has_package_access(self, package):
        """Check if user has access to the package"""
        try:
            PackageSubscription.objects.get(
                user=self.request.user,
                package=package,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            return True
        except PackageSubscription.DoesNotExist:
            return False
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip


class ContentDownloadView(LoginRequiredMixin, DetailView):
    """
    Secure file download with package access control
    """
    model = Content
    pk_url_kwarg = 'content_id'
    
    def get(self, request, *args, **kwargs):
        """Handle file download request"""
        content = self.get_object()
        
        # Check package access
        if not self.has_package_access(content.package):
            return HttpResponseForbidden("No access to this package")
        
        # Check if file exists
        if not content.file_attachment:
            return HttpResponseForbidden("No file available for download")
        
        # Increment download count
        content.download_count += 1
        content.save(update_fields=['download_count'])
        
        # Log download activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='content_download',
            description=f'Downloaded file: {content.title}',
            content=content,
            package=content.package,
            ip_address=self.get_client_ip(),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        # Return file response
        try:
            response = FileResponse(
                content.file_attachment.open(),
                as_attachment=True,
                filename=content.file_attachment.name.split('/')[-1]
            )
            return response
        except Exception as e:
            logger.error(f"File download error: {e}")
            return HttpResponseForbidden("File not available")
    
    def has_package_access(self, package):
        """Check if user has access to the package"""
        try:
            PackageSubscription.objects.get(
                user=self.request.user,
                package=package,
                is_active=True,
                expires_at__gt=timezone.now()
            )
            return True
        except PackageSubscription.DoesNotExist:
            return False
    
    def get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
