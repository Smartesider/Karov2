"""
Admin configuration for JuridiskPorten
Secure admin interface for managing legal content and users
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from django.db import models
from ckeditor.widgets import CKEditorWidget
from .models import (
    User, LegalPackage, PackageSubscription, 
    ContentCategory, Content, UserActivity,
    ContentBookmark, UserProgress, ContentVersion, PackageAccess,
    # Phase 3: E-commerce models
    ShoppingCart, CartItem, Order, OrderItem, Coupon, PaymentIntent
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Enhanced user admin with role-based features
    """
    list_display = [
        'email', 'get_full_name', 'role', 'organization', 
        'is_verified', 'is_active', 'last_activity', 'created_at'
    ]
    list_filter = ['role', 'is_verified', 'is_active', 'created_at', 'gdpr_consent']
    search_fields = ['email', 'first_name', 'last_name', 'organization']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('JuridiskPorten Info', {
            'fields': ('role', 'phone', 'organization', 'is_verified')
        }),
        ('Privacy & Consent', {
            'fields': ('accepts_marketing', 'gdpr_consent', 'gdpr_consent_date')
        }),
        ('Activity', {
            'fields': ('last_activity', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_activity']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related()
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.email
    get_full_name.short_description = 'Full Name'


@admin.register(LegalPackage)
class LegalPackageAdmin(admin.ModelAdmin):
    """
    Admin interface for legal packages
    """
    list_display = [
        'name', 'package_type', 'price', 'is_active', 
        'active_subscribers_count', 'sort_order', 'created_at'
    ]
    list_filter = ['package_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'package_type', 'slug', 'description', 'detailed_description')
        }),
        ('Pricing & Access', {
            'fields': ('price', 'trial_period_days', 'is_active', 'sort_order')
        }),
        ('Appearance', {
            'fields': ('color_primary', 'icon', 'features')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'slug']
    prepopulated_fields = {'slug': ('package_type',)}
    
    def active_subscribers_count(self, obj):
        count = obj.active_subscribers_count
        if count > 0:
            url = reverse('admin:core_packagesubscription_changelist')
            return format_html(
                '<a href="{}?package__id__exact={}">{}</a>',
                url, obj.id, count
            )
        return count
    active_subscribers_count.short_description = 'Active Subscribers'


@admin.register(PackageSubscription)
class PackageSubscriptionAdmin(admin.ModelAdmin):
    """
    Admin interface for package subscriptions
    """
    list_display = [
        'user', 'package', 'status', 'is_active', 
        'starts_at', 'expires_at', 'days_remaining', 'price_paid'
    ]
    list_filter = ['status', 'is_active', 'package', 'starts_at', 'expires_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'package__name']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Subscription Details', {
            'fields': ('user', 'package', 'status', 'is_active')
        }),
        ('Duration', {
            'fields': ('starts_at', 'expires_at', 'auto_renew')
        }),
        ('Billing', {
            'fields': ('price_paid', 'payment_reference')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def days_remaining(self, obj):
        days = obj.days_remaining
        if days <= 0:
            return format_html('<span style="color: red;">Expired</span>')
        elif days <= 7:
            return format_html('<span style="color: orange;">{} days</span>', days)
        else:
            return f"{days} days"
    days_remaining.short_description = 'Days Remaining'


@admin.register(ContentCategory)
class ContentCategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for content categories
    """
    list_display = ['name', 'category_type', 'is_active', 'sort_order', 'created_at']
    list_filter = ['category_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'slug', 'category_type', 'description')
        }),
        ('Settings', {
            'fields': ('is_active', 'sort_order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    """
    Enhanced admin interface for content management with Phase 2 features
    """
    list_display = [
        'title', 'package', 'category', 'content_type', 'author', 'status', 
        'featured', 'priority', 'view_count', 'average_reading_time', 'published_at'
    ]
    list_filter = [
        'status', 'content_type', 'featured', 'package', 'category', 
        'published_at', 'created_at', 'tags'
    ]
    search_fields = ['title', 'content', 'excerpt', 'meta_description', 'tags__name']
    ordering = ['-priority', '-published_at', '-created_at']
    date_hierarchy = 'published_at'
    filter_horizontal = ('tags',)
    
    fieldsets = (
        ('Content Information', {
            'fields': ('title', 'slug', 'content_type', 'excerpt', 'content')
        }),
        ('Organization', {
            'fields': ('package', 'category', 'author', 'tags')
        }),
        ('Publishing & Status', {
            'fields': ('status', 'featured', 'priority', 'published_at', 'scheduled_publish_at')
        }),
        ('Media & Attachments', {
            'fields': ('image', 'file_attachment')
        }),
        ('Version Control', {
            'fields': ('version', 'previous_version'),
            'classes': ('collapse',)
        }),
        ('SEO & Metadata', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('view_count', 'download_count', 'average_reading_time'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'view_count', 'download_count', 'average_reading_time']
    prepopulated_fields = {'slug': ('title',)}
    
    # Use CKEditor for content field
    formfield_overrides = {
        models.TextField: {'widget': CKEditorWidget(config_name='default')},
    }
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('package', 'category', 'author').prefetch_related('tags')
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "author":
            kwargs["queryset"] = User.objects.filter(role='lawyer')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    actions = ['make_published', 'make_draft', 'make_featured']
    
    def make_published(self, request, queryset):
        """Bulk action to publish selected content"""
        count = queryset.update(status='published', published_at=timezone.now())
        self.message_user(request, f'{count} content items published.')
    
    def make_draft(self, request, queryset):
        """Bulk action to unpublish selected content"""
        count = queryset.update(status='draft')
        self.message_user(request, f'{count} content items set to draft.')
    
    def make_featured(self, request, queryset):
        """Bulk action to feature selected content"""
        count = queryset.update(featured=True)
        self.message_user(request, f'{count} content items marked as featured.')


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """
    Admin interface for user activity tracking
    """
    list_display = [
        'user', 'activity_type', 'description', 'ip_address', 'created_at'
    ]
    list_filter = ['activity_type', 'created_at']
    search_fields = [
        'user__email', 'user__first_name', 'user__last_name', 
        'description', 'ip_address'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Activity Information', {
            'fields': ('user', 'activity_type', 'description')
        }),
        ('Related Objects', {
            'fields': ('content', 'package')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        # Activities should only be created automatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Activities should not be changed
        return False
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'content', 'package')


@admin.register(ContentBookmark)
class ContentBookmarkAdmin(admin.ModelAdmin):
    """
    Admin for user content bookmarks
    """
    list_display = ['user', 'content', 'created_at']
    list_filter = ['created_at', 'content__package', 'content__category']
    search_fields = ['user__email', 'content__title', 'notes']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'content')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'content')


@admin.register(UserProgress)
class UserProgressAdmin(admin.ModelAdmin):
    """
    Admin for tracking user progress through content
    """
    list_display = ['user', 'content', 'status', 'time_spent_display', 'last_accessed']
    list_filter = ['status', 'content__package', 'content__category', 'started_at', 'completed_at']
    search_fields = ['user__email', 'content__title']
    readonly_fields = ['created_at', 'updated_at', 'last_accessed']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'content', 'status')
        }),
        ('Progress Tracking', {
            'fields': ('started_at', 'completed_at', 'time_spent', 'last_accessed')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def time_spent_display(self, obj):
        """Display time spent in a readable format"""
        if obj.time_spent:
            minutes = obj.time_spent // 60
            seconds = obj.time_spent % 60
            return f"{minutes}m {seconds}s"
        return "0m 0s"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'content')


@admin.register(ContentVersion)
class ContentVersionAdmin(admin.ModelAdmin):
    """
    Admin for content version history
    """
    list_display = ['content', 'version_number', 'author', 'change_summary', 'created_at']
    list_filter = ['created_at', 'content__package', 'author']
    search_fields = ['content__title', 'author__email', 'change_summary']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {
            'fields': ('content', 'version_number', 'author')
        }),
        ('Version Details', {
            'fields': ('title', 'change_summary')
        }),
        ('Content Snapshot', {
            'fields': ('content_data', 'excerpt')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('content', 'author')
    
    def has_add_permission(self, request):
        # Versions should be created automatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Versions should not be changed once created
        return False


@admin.register(PackageAccess)
class PackageAccessAdmin(admin.ModelAdmin):
    """
    Admin for detailed package access analytics
    """
    list_display = ['user', 'package', 'session_duration_display', 'pages_viewed', 'created_at']
    list_filter = ['package', 'created_at']
    search_fields = ['user__email', 'package__name']
    readonly_fields = ['created_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'package')
        }),
        ('Session Data', {
            'fields': ('session_duration', 'pages_viewed', 'content_accessed')
        }),
        ('Request Information', {
            'fields': ('ip_address', 'user_agent', 'referrer')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        }),
    )
    
    def session_duration_display(self, obj):
        """Display session duration in a readable format"""
        if obj.session_duration:
            minutes = obj.session_duration // 60
            seconds = obj.session_duration % 60
            return f"{minutes}m {seconds}s"
        return "0m 0s"
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'package').prefetch_related('content_accessed')
    
    def has_add_permission(self, request):
        # Access records should only be created automatically
        return False
    
    def has_change_permission(self, request, obj=None):
        # Access records should not be changed
        return False


# ==============================================================================
# PHASE 3: E-COMMERCE ADMIN CLASSES
# ==============================================================================

class CartItemInline(admin.TabularInline):
    """
    Inline admin for cart items
    """
    model = CartItem
    extra = 0
    readonly_fields = ['price', 'total_price', 'created_at']
    fields = ['package', 'quantity', 'price', 'total_price', 'created_at']
    
    def total_price(self, obj):
        return f"{obj.total_price} kr" if obj else "0 kr"
    total_price.short_description = 'Total'


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    """
    Admin for shopping carts
    """
    list_display = ['id', 'user_display', 'item_count', 'total_price_display', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__email', 'session_key']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [CartItemInline]
    
    fieldsets = (
        (None, {
            'fields': ('user', 'session_key')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        if obj.user:
            return obj.user.get_full_name()
        return f"Anonymous ({obj.session_key[:8]}...)"
    user_display.short_description = 'User'
    
    def total_price_display(self, obj):
        return f"{obj.total_price} kr"
    total_price_display.short_description = 'Total'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('items', 'items__package')


class OrderItemInline(admin.TabularInline):
    """
    Inline admin for order items
    """
    model = OrderItem
    extra = 0
    readonly_fields = ['package', 'quantity', 'price', 'total_price', 'created_at']
    fields = ['package', 'quantity', 'price', 'total_price', 'created_at']
    
    def total_price(self, obj):
        return f"{obj.total_price} kr" if obj else "0 kr"
    total_price.short_description = 'Total'
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """
    Admin for orders with comprehensive management features
    """
    list_display = [
        'order_number', 'user', 'status', 'payment_status', 
        'final_amount_display', 'created_at', 'paid_at'
    ]
    list_filter = [
        'status', 'payment_status', 'created_at', 'paid_at', 
        'billing_country'
    ]
    search_fields = [
        'order_number', 'user__email', 'billing_email', 
        'billing_name', 'stripe_payment_intent_id'
    ]
    readonly_fields = [
        'order_number', 'stripe_payment_intent_id', 'stripe_customer_id',
        'created_at', 'updated_at', 'paid_at', 'completed_at'
    ]
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Amounts', {
            'fields': ('total_amount', 'tax_amount', 'discount_amount', 'final_amount')
        }),
        ('Billing Information', {
            'fields': (
                'billing_name', 'billing_email', 'billing_organization',
                'billing_address', 'billing_city', 'billing_postal_code', 'billing_country'
            )
        }),
        ('Payment Details', {
            'fields': (
                'stripe_payment_intent_id', 'stripe_customer_id', 
                'payment_method', 'coupon_code'
            ),
            'classes': ('collapse',)
        }),
        ('Notes', {
            'fields': ('customer_notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_completed', 'export_orders']
    
    def final_amount_display(self, obj):
        return f"{obj.final_amount} kr"
    final_amount_display.short_description = 'Amount'
    
    def mark_as_completed(self, request, queryset):
        """Bulk action to mark orders as completed"""
        updated = 0
        for order in queryset:
            if order.payment_status == 'succeeded' and order.status != 'completed':
                order.status = 'completed'
                order.completed_at = timezone.now()
                order.save()
                updated += 1
        
        self.message_user(request, f'{updated} orders marked as completed.')
    mark_as_completed.short_description = 'Mark selected orders as completed'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user').prefetch_related('items', 'items__package')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """
    Admin for discount coupons
    """
    list_display = [
        'code', 'name', 'coupon_type', 'discount_value_display',
        'usage_display', 'is_active', 'valid_from', 'valid_until'
    ]
    list_filter = ['coupon_type', 'is_active', 'valid_from', 'valid_until', 'created_at']
    search_fields = ['code', 'name', 'description']
    readonly_fields = ['used_count', 'created_at', 'updated_at']
    filter_horizontal = ['applicable_packages']
    date_hierarchy = 'valid_from'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description', 'is_active')
        }),
        ('Discount Details', {
            'fields': (
                'coupon_type', 'discount_value', 'minimum_order_amount', 
                'maximum_discount_amount'
            )
        }),
        ('Usage Limits', {
            'fields': ('usage_limit', 'usage_limit_per_user', 'used_count')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Package Restrictions', {
            'fields': ('applicable_packages',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_coupons', 'deactivate_coupons', 'export_coupons']
    
    def discount_value_display(self, obj):
        if obj.coupon_type == 'percentage':
            return f"{obj.discount_value}%"
        else:
            return f"{obj.discount_value} kr"
    discount_value_display.short_description = 'Discount'
    
    def usage_display(self, obj):
        if obj.usage_limit:
            return f"{obj.used_count}/{obj.usage_limit}"
        return f"{obj.used_count}/∞"
    usage_display.short_description = 'Usage'
    
    def activate_coupons(self, request, queryset):
        """Bulk action to activate coupons"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} coupons activated.')
    activate_coupons.short_description = 'Activate selected coupons'
    
    def deactivate_coupons(self, request, queryset):
        """Bulk action to deactivate coupons"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} coupons deactivated.')
    deactivate_coupons.short_description = 'Deactivate selected coupons'


@admin.register(PaymentIntent)
class PaymentIntentAdmin(admin.ModelAdmin):
    """
    Admin for payment intents (Stripe tracking)
    """
    list_display = [
        'stripe_payment_intent_id', 'order', 'amount_display', 
        'currency', 'status', 'payment_method_type', 'created_at'
    ]
    list_filter = ['status', 'currency', 'payment_method_type', 'created_at']
    search_fields = [
        'stripe_payment_intent_id', 'order__order_number', 
        'order__user__email'
    ]
    readonly_fields = [
        'stripe_payment_intent_id', 'order', 'amount', 'currency',
        'status', 'payment_method_type', 'last_four', 'webhook_data',
        'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Payment Intent', {
            'fields': (
                'stripe_payment_intent_id', 'order', 'amount', 
                'currency', 'status'
            )
        }),
        ('Payment Method', {
            'fields': ('payment_method_type', 'last_four'),
            'classes': ('collapse',)
        }),
        ('Webhook Data', {
            'fields': ('webhook_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def amount_display(self, obj):
        return f"{obj.amount / 100:.2f} {obj.currency.upper()}"
    amount_display.short_description = 'Amount'
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('order', 'order__user')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


# Customize admin site
admin.site.site_header = 'JuridiskPorten Administration'
admin.site.site_title = 'JuridiskPorten Admin'
admin.site.index_title = 'Legal Services Platform Management'
