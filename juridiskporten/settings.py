"""
Django settings for JuridiskPorten project.
Legal Services Platform with Package-based Access Control

Security-first configuration with environment-based settings
"""

from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security Configuration
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS_STR = config('ALLOWED_HOSTS', default='localhost')
ALLOWED_HOSTS = ALLOWED_HOSTS_STR.split(',') if isinstance(ALLOWED_HOSTS_STR, str) else ['localhost']

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'corsheaders',
    'ckeditor',
    'ckeditor_uploader',
    'taggit',
    'widget_tweaks',
    'django_cleanup.apps.CleanupConfig',
    'django_extensions',
]

LOCAL_APPS = [
    'core',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.PackageAccessMiddleware',
]

ROOT_URLCONF = 'juridiskporten.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.site_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'juridiskporten.wsgi.application'

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Custom User Model
AUTH_USER_MODEL = 'core.User'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'core.validators.CustomPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'nb-no'
TIME_ZONE = 'Europe/Oslo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = config('STATIC_ROOT', default=BASE_DIR / 'staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = config('MEDIA_ROOT', default=BASE_DIR / 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Security Settings
SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
X_FRAME_OPTIONS = config('X_FRAME_OPTIONS', default='DENY')

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Session Configuration
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = 'noreply@skycode.no'

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# JuridiskPorten Specific Settings
LEGAL_PACKAGES = {
    'bevillingsforvaltning': {
        'name': 'Saksbehandlerstøtte – bevillingsforvaltning',
        'description': 'Ressurser for skjenking, taxi, servering m.m.',
        'color': '#3E4D50',
    },
    'arbeidsrett': {
        'name': 'Saksbehandlerstøtte – arbeidsrett & HR',
        'description': 'HR, ledere, personalansvar',
        'color': '#A7B9BC',
    },
    'forvaltningsrett': {
        'name': 'Saksbehandlerstøtte – generell forvaltningsrett',
        'description': 'Offentlig og privat saksbehandling',
        'color': '#D3B16D',
    },
    'helse': {
        'name': 'Saksbehandlerstøtte – helse og pasient/brukerrettigheter',
        'description': 'Helsepersonell, pårørende, brukerstøtte',
        'color': '#6D8B74',
    },
}

# CKEditor Configuration
CKEDITOR_UPLOAD_PATH = "uploads/"
CKEDITOR_IMAGE_BACKEND = "pillow"
CKEDITOR_JQUERY_URL = 'https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js'

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['Link', 'Unlink'],
            ['RemoveFormat', 'Source'],
            ['Image', 'Table'],
            ['Styles', 'Format', 'Font', 'FontSize'],
        ],
        'height': 300,
        'width': '100%',
        'toolbarCanCollapse': True,
        'forcePasteAsPlainText': True,
    },
    'minimal': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic'],
            ['Link', 'Unlink'],
            ['RemoveFormat'],
        ],
        'height': 150,
        'width': '100%',
    }
}

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Allowed file extensions for content uploads
ALLOWED_CONTENT_FILE_EXTENSIONS = [
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'txt', 'rtf', 'odt', 'ods', 'odp'
]

ALLOWED_IMAGE_EXTENSIONS = [
    'jpg', 'jpeg', 'png', 'gif', 'svg', 'webp'
]

# Content Management Settings
CONTENT_PAGINATION_SIZE = 12
SEARCH_RESULTS_PER_PAGE = 10
MAX_CONTENT_EXCERPT_LENGTH = 200

# ==============================================================================
# PHASE 3: STRIPE PAYMENT SETTINGS
# ==============================================================================

# Stripe API Keys (get these from Stripe Dashboard)
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# Payment Settings
DEFAULT_CURRENCY = 'NOK'
STRIPE_CURRENCY = 'nok'

# Tax Settings (Norwegian VAT)
DEFAULT_TAX_RATE = 0.25  # 25% Norwegian VAT
TAX_DISPLAY_PRICES_INCLUSIVE = True

# Order Settings
ORDER_NUMBER_PREFIX = 'KAR'
ORDER_EXPIRY_MINUTES = 30  # Payment intent expires after 30 minutes

# Shopping Cart Settings
CART_SESSION_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days
CART_ANONYMOUS_USER_EXPIRE_DAYS = 7

# Coupon Settings
COUPON_CODE_LENGTH = 8
COUPON_DEFAULT_USAGE_LIMIT = 100

# Email Settings for Order Confirmations
ORDER_CONFIRMATION_FROM_EMAIL = config('ORDER_FROM_EMAIL', default='noreply@juridiskporten.no')
ORDER_NOTIFICATION_EMAIL = config('ORDER_NOTIFICATION_EMAIL', default='orders@juridiskporten.no')

# Payment Processing
PAYMENT_SUCCESS_REDIRECT_URL = '/payment/success/'
PAYMENT_CANCEL_REDIRECT_URL = '/cart/'
