"""
URL configuration for core app
Enhanced with Phase 2 and Phase 3 features
"""

from django.urls import path
from . import views
from .views_phase2 import (
    EnhancedPackageListView, PackageDetailView as Phase2PackageDetailView,
    ContentListView, ContentDetailView as Phase2ContentDetailView,
    toggle_bookmark, mark_content_complete, UserBookmarksView, SearchView
)
from .views_phase3 import (
    PackageShowcaseView, PackageDetailView as Phase3PackageDetailView,
    ShoppingCartView, CheckoutView, PaymentProcessingView, PaymentSuccessView,
    OrderHistoryView, OrderDetailView, stripe_webhook,
    add_to_cart, remove_from_cart, apply_coupon, cart_count
)

app_name = 'core'

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('password/reset/', views.PasswordResetView.as_view(), name='password_reset'),
    
    # Dashboard and profile
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    
    # Enhanced Package URLs (Phase 2)
    path('packages/', EnhancedPackageListView.as_view(), name='package_list'),
    path('packages/<slug:slug>/', Phase2PackageDetailView.as_view(), name='package_detail'),
    
    # Enhanced Content URLs (Phase 2)
    path('packages/<slug:package_slug>/content/', ContentListView.as_view(), name='content_list'),
    path('packages/<slug:package_slug>/content/<slug:content_slug>/', 
         Phase2ContentDetailView.as_view(), name='content_detail'),
    
    # File download
    path('download/<uuid:content_id>/', views.ContentDownloadView.as_view(), name='content_download'),
    
    # AJAX endpoints
    path('ajax/bookmark/', toggle_bookmark, name='toggle_bookmark'),
    path('ajax/complete/', mark_content_complete, name='mark_content_complete'),
    
    # User features
    path('bookmarks/', UserBookmarksView.as_view(), name='user_bookmarks'),
    path('search/', SearchView.as_view(), name='search'),
    
    # ==============================================================================
    # PHASE 3: E-COMMERCE & PAYMENT URLS
    # ==============================================================================
    
    # Package showcase and e-commerce
    path('shop/', PackageShowcaseView.as_view(), name='package_showcase'),
    path('shop/<slug:slug>/', Phase3PackageDetailView.as_view(), name='package_detail_shop'),
    
    # Shopping cart
    path('cart/', ShoppingCartView.as_view(), name='shopping_cart'),
    path('cart/add/<uuid:package_id>/', add_to_cart, name='add_to_cart'),
    path('cart/remove/<uuid:package_id>/', remove_from_cart, name='remove_from_cart'),
    path('cart/count/', cart_count, name='cart_count'),
    
    # Checkout and payment
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('payment/processing/', PaymentProcessingView.as_view(), name='payment_processing'),
    path('payment/success/', PaymentSuccessView.as_view(), name='payment_success'),
    
    # Coupons
    path('apply-coupon/', apply_coupon, name='apply_coupon'),
    
    # Order management
    path('orders/', OrderHistoryView.as_view(), name='order_history'),
    path('orders/<uuid:pk>/', OrderDetailView.as_view(), name='order_detail'),
    
    # Stripe webhook
    path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
]
