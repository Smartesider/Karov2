"""
Enhanced views for Phase 2: Package Management & Content System
Advanced content browsing, search, bookmarks, and dashboard features
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Q, Count, Avg, F
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import logging

from .models import (
    LegalPackage, Content, ContentCategory, ContentBookmark, 
    UserProgress, PackageAccess, PackageSubscription
)
from .decorators import package_access_required

logger = logging.getLogger(__name__)


class EnhancedPackageListView(ListView):
    """
    Enhanced package listing with filtering and sorting
    """
    model = LegalPackage
    template_name = 'core/packages/list.html'
    context_object_name = 'packages'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = LegalPackage.objects.filter(is_active=True)
        
        # Filter by access level if user is authenticated
        if self.request.user.is_authenticated:
            user_packages = PackageSubscription.objects.filter(
                user=self.request.user, 
                is_active=True,
                expires_at__gt=timezone.now()
            ).values_list('package_id', flat=True)
            
            # Add annotation for user access
            queryset = queryset.extra(
                select={'user_has_access': f'id IN ({",".join(map(str, user_packages)) or "NULL"})'}
            )
        
        # Add content count and subscriber count
        queryset = queryset.annotate(
            content_count=Count('contents', filter=Q(contents__status='published')),
            subscriber_count=Count('packagesubscription', 
                                 filter=Q(packagesubscription__is_active=True))
        )
        
        return queryset.order_by('sort_order', 'name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.user.is_authenticated:
            # Get user's active subscriptions
            context['user_subscriptions'] = PackageSubscription.objects.filter(
                user=self.request.user,
                is_active=True,
                expires_at__gt=timezone.now()
            ).select_related('package')
        
        # Package statistics
        context['total_packages'] = LegalPackage.objects.filter(is_active=True).count()
        context['featured_packages'] = LegalPackage.objects.filter(
            is_active=True, is_featured=True
        ).order_by('sort_order')[:3]
        
        return context


class PackageDetailView(DetailView):
    """
    Enhanced package detail view with content preview
    """
    model = LegalPackage
    template_name = 'core/packages/detail.html'
    context_object_name = 'package'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return LegalPackage.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        package = self.object
        user = self.request.user
        
        # Check user access
        has_access = False
        subscription = None
        if user.is_authenticated:
            subscription = PackageSubscription.objects.filter(
                user=user,
                package=package,
                is_active=True,
                expires_at__gt=timezone.now()
            ).first()
            has_access = subscription is not None
        
        context['has_access'] = has_access
        context['subscription'] = subscription
        
        # Content organization by category
        categories = ContentCategory.objects.filter(
            contents__package=package,
            contents__status='published',
            is_active=True
        ).distinct().annotate(
            content_count=Count('contents', filter=Q(contents__status='published'))
        )
        
        context['content_categories'] = categories
        
        # Featured content
        context['featured_content'] = Content.objects.filter(
            package=package,
            status='published',
            featured=True
        ).order_by('-priority', '-published_at')[:6]
        
        # Latest content
        context['latest_content'] = Content.objects.filter(
            package=package,
            status='published'
        ).order_by('-published_at')[:5]
        
        # Package statistics
        context['total_content'] = Content.objects.filter(
            package=package,
            status='published'
        ).count()
        
        # User progress if authenticated and has access
        if has_access:
            context['user_progress'] = UserProgress.objects.filter(
                user=user,
                content__package=package
            ).values('status').annotate(count=Count('id'))
            
            # Recently accessed content
            context['recent_content'] = UserProgress.objects.filter(
                user=user,
                content__package=package
            ).order_by('-last_accessed')[:5].select_related('content')
        
        return context


class ContentListView(LoginRequiredMixin, ListView):
    """
    Content listing within a package with filtering and search
    """
    model = Content
    template_name = 'core/content/list.html'
    context_object_name = 'contents'
    paginate_by = 12
    
    def dispatch(self, request, *args, **kwargs):
        self.package = get_object_or_404(LegalPackage, slug=kwargs['package_slug'])
        
        # Check package access
        if not self.package.user_has_access(request.user):
            return HttpResponseForbidden("Access denied to this package")
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Content.objects.filter(
            package=self.package,
            status='published'
        ).select_related('category', 'author').prefetch_related('tags')
        
        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(excerpt__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()
        
        # Filter by content type
        content_type = self.request.GET.get('type', '')
        if content_type:
            queryset = queryset.filter(content_type=content_type)
        
        # Filter by category
        category_id = self.request.GET.get('category', '')
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Sorting
        sort_by = self.request.GET.get('sort', 'priority')
        if sort_by == 'newest':
            queryset = queryset.order_by('-published_at')
        elif sort_by == 'oldest':
            queryset = queryset.order_by('published_at')
        elif sort_by == 'title':
            queryset = queryset.order_by('title')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-view_count')
        else:  # priority (default)
            queryset = queryset.order_by('-priority', '-published_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['package'] = self.package
        
        # Filter options
        context['content_types'] = Content.CONTENT_TYPES
        context['categories'] = ContentCategory.objects.filter(
            contents__package=self.package,
            is_active=True
        ).distinct()
        
        # Current filters
        context['current_search'] = self.request.GET.get('search', '')
        context['current_type'] = self.request.GET.get('type', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_sort'] = self.request.GET.get('sort', 'priority')
        
        # User bookmarks for this package
        if self.request.user.is_authenticated:
            bookmarked_content_ids = ContentBookmark.objects.filter(
                user=self.request.user,
                content__package=self.package
            ).values_list('content_id', flat=True)
            context['bookmarked_content_ids'] = list(bookmarked_content_ids)
        
        return context


class ContentDetailView(LoginRequiredMixin, DetailView):
    """
    Enhanced content detail view with progress tracking
    """
    model = Content
    template_name = 'core/content/detail.html'
    context_object_name = 'content'
    slug_field = 'slug'
    slug_url_kwarg = 'content_slug'
    
    def dispatch(self, request, *args, **kwargs):
        self.package = get_object_or_404(LegalPackage, slug=kwargs['package_slug'])
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        return Content.objects.filter(
            package=self.package,
            status='published'
        ).select_related('category', 'author', 'package')
    
    @method_decorator(package_access_required)
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        
        # Track content view
        content = self.object
        
        # Update view count
        Content.objects.filter(id=content.id).update(
            view_count=F('view_count') + 1
        )
        
        # Track user progress
        if request.user.is_authenticated:
            progress, created = UserProgress.objects.get_or_create(
                user=request.user,
                content=content,
                defaults={'started_at': timezone.now(), 'status': 'in_progress'}
            )
            
            if not progress.started_at:
                progress.mark_started()
        
        return response
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content = self.object
        user = self.request.user
        
        context['package'] = self.package
        
        # User interaction data
        if user.is_authenticated:
            # Check if bookmarked
            context['is_bookmarked'] = ContentBookmark.objects.filter(
                user=user, content=content
            ).exists()
            
            # User progress
            context['user_progress'] = UserProgress.objects.filter(
                user=user, content=content
            ).first()
        
        # Related content
        context['related_content'] = Content.objects.filter(
            package=self.package,
            category=content.category,
            status='published'
        ).exclude(id=content.id).order_by('-priority', '-published_at')[:4]
        
        # Content navigation (prev/next)
        all_content = list(Content.objects.filter(
            package=self.package,
            status='published'
        ).order_by('-priority', '-published_at').values_list('slug', flat=True))
        
        try:
            current_index = all_content.index(content.slug)
            context['prev_content'] = all_content[current_index + 1] if current_index + 1 < len(all_content) else None
            context['next_content'] = all_content[current_index - 1] if current_index > 0 else None
        except (ValueError, IndexError):
            pass
        
        return context


@login_required
@require_POST
def toggle_bookmark(request):
    """
    AJAX endpoint to toggle content bookmark
    """
    try:
        content_id = request.POST.get('content_id')
        content = get_object_or_404(Content, id=content_id)
        
        # Check package access
        if not content.package.user_has_access(request.user):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        bookmark, created = ContentBookmark.objects.get_or_create(
            user=request.user,
            content=content
        )
        
        if created:
            return JsonResponse({
                'status': 'bookmarked',
                'message': 'Content bookmarked'
            })
        else:
            bookmark.delete()
            return JsonResponse({
                'status': 'removed',
                'message': 'Bookmark removed'
            })
    
    except Exception as e:
        logger.error(f"Bookmark toggle error: {e}")
        return JsonResponse({'error': 'Server error'}, status=500)


@login_required
@require_POST
def mark_content_complete(request):
    """
    AJAX endpoint to mark content as completed
    """
    try:
        content_id = request.POST.get('content_id')
        content = get_object_or_404(Content, id=content_id)
        
        # Check package access
        if not content.package.user_has_access(request.user):
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        progress, created = UserProgress.objects.get_or_create(
            user=request.user,
            content=content
        )
        
        progress.mark_completed()
        
        return JsonResponse({
            'status': 'completed',
            'message': 'Content marked as completed'
        })
    
    except Exception as e:
        logger.error(f"Mark complete error: {e}")
        return JsonResponse({'error': 'Server error'}, status=500)


class UserBookmarksView(LoginRequiredMixin, ListView):
    """
    User's bookmarked content across all packages
    """
    model = ContentBookmark
    template_name = 'core/user/bookmarks.html'
    context_object_name = 'bookmarks'
    paginate_by = 20
    
    def get_queryset(self):
        return ContentBookmark.objects.filter(
            user=self.request.user
        ).select_related('content', 'content__package', 'content__category').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Group bookmarks by package
        bookmarks_by_package = {}
        for bookmark in context['bookmarks']:
            package = bookmark.content.package
            if package not in bookmarks_by_package:
                bookmarks_by_package[package] = []
            bookmarks_by_package[package].append(bookmark)
        
        context['bookmarks_by_package'] = bookmarks_by_package
        
        return context


class SearchView(LoginRequiredMixin, TemplateView):
    """
    Global search across all accessible content
    """
    template_name = 'core/search/results.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        query = self.request.GET.get('q', '').strip()
        context['query'] = query
        
        if query and len(query) >= 3:
            # Get user's accessible packages
            accessible_packages = PackageSubscription.objects.filter(
                user=self.request.user,
                is_active=True,
                expires_at__gt=timezone.now()
            ).values_list('package_id', flat=True)
            
            # Search content
            content_results = Content.objects.filter(
                package_id__in=accessible_packages,
                status='published'
            ).filter(
                Q(title__icontains=query) |
                Q(content__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct().select_related('package', 'category')[:50]
            
            context['content_results'] = content_results
            context['total_results'] = content_results.count()
        else:
            context['content_results'] = []
            context['total_results'] = 0
        
        return context
