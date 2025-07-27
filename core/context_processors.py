"""
Context processors for JuridiskPorten
Provide global template context variables
"""

from django.conf import settings
from .models import LegalPackage


def site_context(request):
    """
    Add site-wide context variables to all templates
    """
    context = {
        'site_name': 'JuridiskPorten',
        'site_description': 'Digital legal services platform',
        'site_version': '1.0.0',
        'legal_packages': settings.LEGAL_PACKAGES,
    }
    
    # Add user's active packages if authenticated
    if request.user.is_authenticated:
        try:
            active_packages = request.user.get_active_packages()
            context['user_active_packages'] = active_packages
            context['user_package_types'] = [
                sub.package.package_type for sub in active_packages
            ]
        except Exception:
            context['user_active_packages'] = []
            context['user_package_types'] = []
    
    return context
