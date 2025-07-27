"""
Custom decorators for JuridiskPorten
Package access control and other utility decorators
"""

from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import LegalPackage, PackageSubscription
from django.utils import timezone


def package_access_required(view_func):
    """
    Decorator to check if user has access to the package
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Get package from URL kwargs
        package_slug = kwargs.get('package_slug')
        if package_slug:
            package = get_object_or_404(LegalPackage, slug=package_slug)
            
            # Check if user has active subscription
            has_access = PackageSubscription.objects.filter(
                user=request.user,
                package=package,
                is_active=True,
                expires_at__gt=timezone.now()
            ).exists()
            
            if not has_access:
                return HttpResponseForbidden("You don't have access to this package.")
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


def lawyer_required(view_func):
    """
    Decorator to restrict access to lawyers only
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_lawyer:
            return HttpResponseForbidden("Access restricted to lawyers only.")
        return view_func(request, *args, **kwargs)
    
    return wrapper


def admin_required(view_func):
    """
    Decorator to restrict access to administrators only
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not (request.user.role == 'admin' or request.user.is_superuser):
            return HttpResponseForbidden("Access restricted to administrators only.")
        return view_func(request, *args, **kwargs)
    
    return wrapper
