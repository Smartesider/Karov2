"""
Middleware for JuridiskPorten
Package access control and security middleware
"""

from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import logout
from .models import UserActivity
import logging

logger = logging.getLogger(__name__)


class PackageAccessMiddleware(MiddlewareMixin):
    """
    Middleware to control access to package-specific content
    Redirects users without appropriate package access
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Check package access before processing the request
        """
        # Skip for anonymous users
        if not request.user.is_authenticated:
            return None
        
        # Skip for admin users
        if request.user.is_staff or request.user.is_superuser:
            return None
        
        # Skip for API requests (handle differently)
        if request.path.startswith('/api/'):
            return None
        
        # Skip for authentication and public URLs
        public_urls = [
            '/login/', '/logout/', '/register/', '/password/', 
            '/admin/', '/static/', '/media/', '/'
        ]
        
        if any(request.path.startswith(url) for url in public_urls):
            return None
        
        # Check package-specific URLs
        package_urls = {
            '/bevillingsforvaltning/': 'bevillingsforvaltning',
            '/arbeidsrett/': 'arbeidsrett', 
            '/forvaltningsrett/': 'forvaltningsrett',
            '/helse/': 'helse',
        }
        
        for url_pattern, package_type in package_urls.items():
            if request.path.startswith(url_pattern):
                if not self._has_package_access(request.user, package_type):
                    logger.warning(
                        f"Access denied for user {request.user.email} "
                        f"to package {package_type}"
                    )
                    
                    # Log the access attempt
                    UserActivity.objects.create(
                        user=request.user,
                        activity_type='package_access',
                        description=f'Denied access to {package_type}',
                        ip_address=self._get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    # Redirect to package purchase page or dashboard
                    return redirect('dashboard')
        
        return None
    
    def _has_package_access(self, user, package_type):
        """
        Check if user has active access to the specified package
        """
        try:
            from .models import LegalPackage, PackageSubscription
            
            package = LegalPackage.objects.get(
                package_type=package_type, 
                is_active=True
            )
            
            subscription = PackageSubscription.objects.filter(
                user=user,
                package=package,
                is_active=True,
                expires_at__gt=timezone.now()
            ).first()
            
            return subscription is not None
            
        except Exception as e:
            logger.error(f"Error checking package access: {e}")
            return False
    
    def _get_client_ip(self, request):
        """
        Get the client's IP address from the request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add security headers to all responses
    """
    
    def process_response(self, request, response):
        """
        Add security headers to the response
        """
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://js.stripe.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https://api.stripe.com; "
            "frame-src https://js.stripe.com; "
        )
        
        # Additional security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class ActivityTrackingMiddleware(MiddlewareMixin):
    """
    Track user activity for analytics and security
    """
    
    def process_request(self, request):
        """
        Update user's last activity timestamp
        """
        if request.user.is_authenticated:
            # Update last activity (do this asynchronously in production)
            request.user.last_activity = timezone.now()
            request.user.save(update_fields=['last_activity'])
        
        return None


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple rate limiting middleware
    In production, use Redis-based rate limiting
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = {}  # In production, use Redis
        super().__init__(get_response)
    
    def process_request(self, request):
        """
        Check rate limits for the current request
        """
        ip = self._get_client_ip(request)
        current_time = timezone.now()
        
        # Clean old entries (keep last hour)
        cutoff_time = current_time - timezone.timedelta(hours=1)
        self.request_counts = {
            key: timestamps for key, timestamps in self.request_counts.items()
            if any(ts > cutoff_time for ts in timestamps)
        }
        
        # Check current IP's request count
        if ip not in self.request_counts:
            self.request_counts[ip] = []
        
        # Remove old timestamps
        self.request_counts[ip] = [
            ts for ts in self.request_counts[ip] 
            if ts > cutoff_time
        ]
        
        # Check rate limit (100 requests per hour for anonymous, 1000 for authenticated)
        limit = 1000 if request.user.is_authenticated else 100
        
        if len(self.request_counts[ip]) >= limit:
            logger.warning(f"Rate limit exceeded for IP {ip}")
            return JsonResponse(
                {'error': 'Rate limit exceeded. Please try again later.'}, 
                status=429
            )
        
        # Add current request
        self.request_counts[ip].append(current_time)
        
        return None
    
    def _get_client_ip(self, request):
        """
        Get the client's IP address from the request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class SessionSecurityMiddleware(MiddlewareMixin):
    """
    Enhanced session security
    """
    
    def process_request(self, request):
        """
        Check session security
        """
        if not request.user.is_authenticated:
            return None
        
        # Check if user agent changed (potential session hijacking)
        session_user_agent = request.session.get('user_agent')
        current_user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        if session_user_agent is None:
            request.session['user_agent'] = current_user_agent
        elif session_user_agent != current_user_agent:
            logger.warning(
                f"User agent mismatch for user {request.user.email}. "
                f"Possible session hijacking."
            )
            logout(request)
            return redirect('login')
        
        # Check session age (force re-login after 24 hours)
        session_start = request.session.get('session_start')
        if session_start is None:
            request.session['session_start'] = timezone.now().isoformat()
        else:
            session_start_time = timezone.datetime.fromisoformat(session_start)
            if timezone.now() - session_start_time > timezone.timedelta(days=1):
                logout(request)
                return redirect('login')
        
        return None
