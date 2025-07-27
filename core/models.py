"""
Core models for JuridiskPorten
Database schema for legal services platform with package-based access control
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.text import slugify
from django.core.validators import MinLengthValidator, EmailValidator, FileExtensionValidator
from django.conf import settings
from ckeditor.fields import RichTextField
from taggit.managers import TaggableManager
from decimal import Decimal
import uuid
import os


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    Supports role-based access and package subscriptions
    """
    USER_ROLES = [
        ('client', 'Client'),
        ('lawyer', 'Lawyer'),
        ('admin', 'Administrator'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    role = models.CharField(max_length=20, choices=USER_ROLES, default='client')
    phone = models.CharField(max_length=15, blank=True)
    organization = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_activity = models.DateTimeField(default=timezone.now)
    
    # Privacy and consent
    accepts_marketing = models.BooleanField(default=False)
    gdpr_consent = models.BooleanField(default=False)
    gdpr_consent_date = models.DateTimeField(null=True, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'core_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role']),
            models.Index(fields=['is_verified']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_lawyer(self):
        return self.role == 'lawyer'
    
    @property
    def is_client(self):
        return self.role == 'client'
    
    def get_active_packages(self):
        """Get all active package subscriptions for this user"""
        return PackageSubscription.objects.filter(
            user=self,
            is_active=True,
            expires_at__gt=timezone.now()
        )


class ContentCategory(models.Model):
    """
    Categories for organizing content within packages
    """
    CATEGORY_TYPES = [
        ('article', 'Article'),
        ('form', 'Form/Template'),
        ('qa', 'Q&A'),
        ('resource', 'Resource'),
        ('event', 'Event'),
        ('checklist', 'Checklist'),
        ('guide', 'Guide'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_content_category'
        verbose_name = 'Content Category'
        verbose_name_plural = 'Content Categories'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['category_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_category_type_display()})"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class LegalPackage(models.Model):
    """
    Legal service packages available for purchase
    Four main packages: bevillingsforvaltning, arbeidsrett, forvaltningsrett, helse
    """
    PACKAGE_TYPES = [
        ('bevillingsforvaltning', 'Saksbehandlerstøtte – bevillingsforvaltning'),
        ('arbeidsrett', 'Saksbehandlerstøtte – arbeidsrett & HR'),
        ('forvaltningsrett', 'Saksbehandlerstøtte – generell forvaltningsrett'),
        ('helse', 'Saksbehandlerstøtte – helse og pasient/brukerrettigheter'),
    ]
    
    ACCESS_LEVELS = [
        ('basic', 'Basic Access'),
        ('standard', 'Standard Access'),
        ('premium', 'Premium Access'),
        ('enterprise', 'Enterprise Access'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    slug = models.SlugField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    package_type = models.CharField(max_length=50, choices=PACKAGE_TYPES, unique=True)
    description = models.TextField()
    detailed_description = RichTextField(config_name='default', blank=True)
    
    # Pricing and access
    price = models.DecimalField(max_digits=10, decimal_places=2)
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    trial_period_days = models.PositiveIntegerField(default=7)
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVELS, default='standard')
    
    # Package features and benefits
    features = models.JSONField(default=list, blank=True, help_text="List of features included in this package")
    benefits = models.JSONField(default=list, blank=True, help_text="Key benefits of this package")
    target_audience = models.JSONField(default=list, blank=True, help_text="Who this package is designed for")
    
    # Visual and branding
    color_primary = models.CharField(max_length=7, default='#3E4D50')  # Hex color
    color_secondary = models.CharField(max_length=7, default='#A7B9BC')  # Hex color
    icon = models.CharField(max_length=50, blank=True)  # Font Awesome class or similar
    banner_image = models.ImageField(upload_to='packages/banners/', blank=True)
    
    # Content organization
    content_categories = models.ManyToManyField(ContentCategory, blank=True, related_name='packages')
    
    # Package settings
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    max_users = models.PositiveIntegerField(default=1, help_text="Maximum users per subscription")
    
    # SEO and marketing
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    testimonials = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_legal_package'
        verbose_name = 'Legal Package'
        verbose_name_plural = 'Legal Packages'
        ordering = ['sort_order', 'name']
        indexes = [
            models.Index(fields=['package_type']),
            models.Index(fields=['is_active']),
            models.Index(fields=['sort_order']),
            models.Index(fields=['is_featured']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.package_type)
        super().save(*args, **kwargs)
    
    @property
    def active_subscribers_count(self):
        """Count of active subscribers"""
        return PackageSubscription.objects.filter(
            package=self,
            is_active=True,
            expires_at__gt=timezone.now()
        ).count()
    
    @property
    def content_count(self):
        """Total published content in this package"""
        from .models import Content  # Avoid circular import
        return Content.objects.filter(package=self, status='published').count()
    
    @property
    def latest_content(self):
        """Get latest published content"""
        from .models import Content  # Avoid circular import
        return Content.objects.filter(package=self, status='published').order_by('-published_at')[:5]
    
    def get_content_by_type(self, content_type):
        """Get published content filtered by type"""
        from .models import Content  # Avoid circular import
        return Content.objects.filter(package=self, status='published', content_type=content_type)
    
    def user_has_access(self, user):
        """Check if user has active access to this package"""
        if not user.is_authenticated:
            return False
        
        return PackageSubscription.objects.filter(
            package=self,
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        ).exists()


class PackageSubscription(models.Model):
    """
    User subscriptions to legal packages
    Tracks access permissions and billing information
    """
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('trial', 'Trial'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(LegalPackage, on_delete=models.CASCADE)
    
    # Subscription details
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='trial')
    is_active = models.BooleanField(default=True)
    starts_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField()
    auto_renew = models.BooleanField(default=False)
    
    # Billing information
    price_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_package_subscription'
        verbose_name = 'Package Subscription'
        verbose_name_plural = 'Package Subscriptions'
        unique_together = ['user', 'package']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['package', 'is_active']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.package.name}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def days_remaining(self):
        if self.is_expired:
            return 0
        return (self.expires_at - timezone.now()).days


class Content(models.Model):
    """
    Main content model for articles, forms, Q&A, etc.
    Associated with packages and categories
    """
    CONTENT_STATUS = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    CONTENT_TYPES = [
        ('article', 'Article'),
        ('form', 'Form/Template'),
        ('qa', 'Q&A'),
        ('resource', 'Resource Document'),
        ('checklist', 'Checklist'),
        ('guide', 'Step-by-step Guide'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200, validators=[MinLengthValidator(5)])
    slug = models.SlugField(max_length=200, unique=True)
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPES, default='article')
    
    # Rich text content
    content = RichTextField(config_name='default')
    excerpt = models.TextField(max_length=500, blank=True, 
                             help_text="Brief summary for listings and search results")
    
    # Relationships
    package = models.ForeignKey(LegalPackage, on_delete=models.CASCADE, related_name='contents')
    category = models.ForeignKey(ContentCategory, on_delete=models.CASCADE, related_name='contents')
    author = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'lawyer'})
    
    # Publishing and scheduling
    status = models.CharField(max_length=20, choices=CONTENT_STATUS, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    scheduled_publish_at = models.DateTimeField(null=True, blank=True, 
                                              help_text="Schedule content for future publication")
    featured = models.BooleanField(default=False)
    priority = models.PositiveIntegerField(default=0, help_text="Higher numbers appear first")
    
    # File attachments with validation
    file_attachment = models.FileField(
        upload_to='content/files/', 
        blank=True,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx'])],
        help_text="PDF, DOC, DOCX, XLS, XLSX files only"
    )
    image = models.ImageField(
        upload_to='content/images/', 
        blank=True,
        help_text="Featured image for the content"
    )
    
    # SEO and metadata
    meta_description = models.CharField(max_length=160, blank=True)
    meta_keywords = models.CharField(max_length=200, blank=True)
    
    # Tags for better organization
    tags = TaggableManager(blank=True, help_text="Add tags separated by commas")
    
    # Analytics and engagement
    view_count = models.PositiveIntegerField(default=0)
    download_count = models.PositiveIntegerField(default=0)
    average_reading_time = models.PositiveIntegerField(default=0, help_text="Estimated reading time in minutes")
    
    # Version control
    version = models.PositiveIntegerField(default=1)
    previous_version = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, 
                                       related_name='newer_versions')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_content'
        verbose_name = 'Content'
        verbose_name_plural = 'Content'
        ordering = ['-priority', '-published_at', '-created_at']
        indexes = [
            models.Index(fields=['package', 'status']),
            models.Index(fields=['category', 'status']),
            models.Index(fields=['author']),
            models.Index(fields=['published_at']),
            models.Index(fields=['featured']),
            models.Index(fields=['content_type']),
            models.Index(fields=['priority']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        
        # Auto-set published_at when status changes to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
            
        # Calculate reading time based on content length
        if self.content:
            word_count = len(self.content.split())
            self.average_reading_time = max(1, word_count // 200)  # 200 words per minute
        
        super().save(*args, **kwargs)
    
    @property
    def is_published(self):
        return self.status == 'published' and self.published_at is not None
    
    @property
    def is_scheduled(self):
        return (self.scheduled_publish_at is not None and 
                self.scheduled_publish_at > timezone.now())
    
    @property
    def file_extension(self):
        if self.file_attachment:
            return os.path.splitext(self.file_attachment.name)[1][1:].upper()
        return None
    
    def get_absolute_url(self):
        return f"/packages/{self.package.slug}/content/{self.slug}/"


class UserActivity(models.Model):
    """
    Audit trail for user activities
    Tracks access to content and package usage
    """
    ACTIVITY_TYPES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('content_view', 'Content Viewed'),
        ('content_download', 'Content Downloaded'),
        ('package_access', 'Package Accessed'),
        ('profile_update', 'Profile Updated'),
        ('subscription_change', 'Subscription Changed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=200)
    
    # Optional relationships for tracking specific objects
    content = models.ForeignKey(Content, on_delete=models.CASCADE, null=True, blank=True)
    package = models.ForeignKey(LegalPackage, on_delete=models.CASCADE, null=True, blank=True)
    
    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_user_activity'
        verbose_name = 'User Activity'
        verbose_name_plural = 'User Activities'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['activity_type']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_activity_type_display()}"


class ContentBookmark(models.Model):
    """
    User bookmarks for content
    Allows users to save content for later reading
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookmarks')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='bookmarked_by')
    notes = models.TextField(blank=True, help_text="Personal notes about this content")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_content_bookmark'
        verbose_name = 'Content Bookmark'
        verbose_name_plural = 'Content Bookmarks'
        unique_together = ['user', 'content']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} bookmarked {self.content.title}"


class UserProgress(models.Model):
    """
    Track user progress through content and packages
    """
    PROGRESS_STATUS = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('bookmarked', 'Bookmarked'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='progress')
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='user_progress')
    status = models.CharField(max_length=20, choices=PROGRESS_STATUS, default='not_started')
    
    # Progress tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_accessed = models.DateTimeField(auto_now=True)
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent in seconds")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_user_progress'
        verbose_name = 'User Progress'
        verbose_name_plural = 'User Progress'
        unique_together = ['user', 'content']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['content', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.content.title} ({self.status})"
    
    def mark_started(self):
        if not self.started_at:
            self.started_at = timezone.now()
            self.status = 'in_progress'
            self.save()
    
    def mark_completed(self):
        self.completed_at = timezone.now()
        self.status = 'completed'
        self.save()


class ContentVersion(models.Model):
    """
    Version control for content
    Maintains history of content changes
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(Content, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField()
    
    # Snapshot of content at this version
    title = models.CharField(max_length=200)
    content_data = models.TextField()
    excerpt = models.TextField(max_length=500, blank=True)
    
    # Change tracking
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    change_summary = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_content_version'
        verbose_name = 'Content Version'
        verbose_name_plural = 'Content Versions'
        unique_together = ['content', 'version_number']
        ordering = ['-version_number']
        indexes = [
            models.Index(fields=['content', 'version_number']),
        ]
    
    def __str__(self):
        return f"{self.content.title} v{self.version_number}"


class PackageAccess(models.Model):
    """
    Track detailed package access patterns
    More granular than UserActivity for analytics
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(LegalPackage, on_delete=models.CASCADE)
    session_duration = models.PositiveIntegerField(default=0, help_text="Session duration in seconds")
    pages_viewed = models.PositiveIntegerField(default=0)
    content_accessed = models.ManyToManyField(Content, blank=True)
    
    # Session metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_package_access'
        verbose_name = 'Package Access'
        verbose_name_plural = 'Package Access Records'
        indexes = [
            models.Index(fields=['user', 'package']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.get_full_name()} accessed {self.package.name}"


# ==============================================================================
# PHASE 3: E-COMMERCE & PAYMENT MODELS
# ==============================================================================

class ShoppingCart(models.Model):
    """
    Shopping cart for users to add packages before purchase
    Supports session-based and user-based carts
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)  # For anonymous users
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_shopping_cart'
        verbose_name = 'Shopping Cart'
        verbose_name_plural = 'Shopping Carts'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['session_key']),
        ]
    
    def __str__(self):
        if self.user:
            return f"Cart for {self.user.get_full_name()}"
        return f"Anonymous Cart ({self.session_key})"
    
    @property
    def total_price(self):
        """Calculate total price of all items in cart"""
        return sum(item.total_price for item in self.items.all())
    
    @property
    def item_count(self):
        """Total number of items in cart"""
        return self.items.count()
    
    def add_package(self, package, quantity=1):
        """Add package to cart or update quantity"""
        item, created = CartItem.objects.get_or_create(
            cart=self,
            package=package,
            defaults={'quantity': quantity, 'price': package.price}
        )
        if not created:
            item.quantity += quantity
            item.save()
        return item
    
    def remove_package(self, package):
        """Remove package from cart"""
        CartItem.objects.filter(cart=self, package=package).delete()
    
    def clear(self):
        """Clear all items from cart"""
        self.items.all().delete()


class CartItem(models.Model):
    """
    Individual items in shopping cart
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(ShoppingCart, on_delete=models.CASCADE, related_name='items')
    package = models.ForeignKey(LegalPackage, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of adding
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_cart_item'
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        unique_together = ['cart', 'package']
        indexes = [
            models.Index(fields=['cart']),
            models.Index(fields=['package']),
        ]
    
    def __str__(self):
        return f"{self.package.name} (x{self.quantity})"
    
    @property
    def total_price(self):
        """Total price for this cart item"""
        return self.price * self.quantity


class Order(models.Model):
    """
    Customer orders for package purchases
    Tracks payment and fulfillment status
    """
    ORDER_STATUS = [
        ('pending', 'Pending Payment'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('succeeded', 'Succeeded'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(max_length=20, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    
    # Order details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    final_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Order status
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    
    # Payment information
    stripe_payment_intent_id = models.CharField(max_length=200, blank=True)
    stripe_customer_id = models.CharField(max_length=200, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    # Customer information
    billing_email = models.EmailField()
    billing_name = models.CharField(max_length=200)
    billing_organization = models.CharField(max_length=200, blank=True)
    billing_address = models.TextField(blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=2, default='NO')  # ISO country code
    
    # Coupon and discount
    coupon_code = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Notes and communication
    customer_notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'core_order'
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.user.get_full_name()}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            from datetime import datetime
            now = datetime.now()
            self.order_number = f"KAR{now.year}{now.month:02d}{now.day:02d}{now.hour:02d}{now.minute:02d}"
            
            # Ensure uniqueness
            counter = 1
            original_number = self.order_number
            while Order.objects.filter(order_number=self.order_number).exists():
                self.order_number = f"{original_number}{counter:02d}"
                counter += 1
        
        super().save(*args, **kwargs)
    
    @property
    def is_paid(self):
        """Check if order is paid"""
        return self.payment_status == 'succeeded'
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled"""
        return self.status in ['pending', 'paid'] and self.payment_status != 'succeeded'
    
    def calculate_total(self):
        """Calculate order total from items"""
        items_total = sum(item.total_price for item in self.items.all())
        self.total_amount = items_total
        self.final_amount = items_total + self.tax_amount - self.discount_amount
        return self.final_amount
    
    def mark_as_paid(self):
        """Mark order as paid and activate subscriptions"""
        self.payment_status = 'succeeded'
        self.status = 'completed'
        self.paid_at = timezone.now()
        self.completed_at = timezone.now()
        self.save()
        
        # Activate package subscriptions
        self.activate_subscriptions()
    
    def activate_subscriptions(self):
        """Activate package subscriptions for paid order"""
        for item in self.items.all():
            # Create or extend subscription
            existing_subscription = PackageSubscription.objects.filter(
                user=self.user,
                package=item.package
            ).first()
            
            if existing_subscription:
                # Extend existing subscription
                if existing_subscription.expires_at > timezone.now():
                    # Extend from current expiry
                    existing_subscription.expires_at += timezone.timedelta(days=365)
                else:
                    # Reactivate from now
                    existing_subscription.expires_at = timezone.now() + timezone.timedelta(days=365)
                existing_subscription.is_active = True
                existing_subscription.status = 'active'
                existing_subscription.save()
            else:
                # Create new subscription
                PackageSubscription.objects.create(
                    user=self.user,
                    package=item.package,
                    status='active',
                    is_active=True,
                    starts_at=timezone.now(),
                    expires_at=timezone.now() + timezone.timedelta(days=365),
                    price_paid=item.price,
                    payment_reference=self.order_number
                )


class OrderItem(models.Model):
    """
    Individual items in an order
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    package = models.ForeignKey(LegalPackage, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of purchase
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_order_item'
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['package']),
        ]
    
    def __str__(self):
        return f"{self.package.name} (x{self.quantity}) - Order {self.order.order_number}"
    
    @property
    def total_price(self):
        """Total price for this order item"""
        return self.price * self.quantity


class Coupon(models.Model):
    """
    Discount coupons for orders
    """
    COUPON_TYPE = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Discount details
    coupon_type = models.CharField(max_length=20, choices=COUPON_TYPE, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)  # % or fixed amount
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    maximum_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Usage limits
    usage_limit = models.PositiveIntegerField(null=True, blank=True, help_text="Total usage limit")
    usage_limit_per_user = models.PositiveIntegerField(default=1, help_text="Usage limit per user")
    used_count = models.PositiveIntegerField(default=0)
    
    # Validity
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    
    # Package restrictions
    applicable_packages = models.ManyToManyField(LegalPackage, blank=True,
                                               help_text="Leave empty for all packages")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_coupon'
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['valid_from', 'valid_until']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def save(self, *args, **kwargs):
        self.code = self.code.upper()  # Always store codes in uppercase
        super().save(*args, **kwargs)
    
    @property
    def is_valid(self):
        """Check if coupon is currently valid"""
        now = timezone.now()
        return (self.is_active and 
                self.valid_from <= now <= self.valid_until and
                (self.usage_limit is None or self.used_count < self.usage_limit))
    
    def can_be_used_by_user(self, user):
        """Check if user can use this coupon"""
        if not self.is_valid:
            return False
        
        user_usage = Order.objects.filter(
            user=user,
            coupon_code=self.code,
            payment_status='succeeded'
        ).count()
        
        return user_usage < self.usage_limit_per_user
    
    def calculate_discount(self, order_amount):
        """Calculate discount amount for given order amount"""
        if order_amount < self.minimum_order_amount:
            return 0
        
        if self.coupon_type == 'percentage':
            discount = order_amount * (self.discount_value / 100)
        else:  # fixed
            discount = self.discount_value
        
        # Apply maximum discount limit if set
        if self.maximum_discount_amount and discount > self.maximum_discount_amount:
            discount = self.maximum_discount_amount
        
        return min(discount, order_amount)  # Can't discount more than order amount
    
    def use_coupon(self):
        """Increment usage count when coupon is used"""
        self.used_count += 1
        self.save(update_fields=['used_count'])


class PaymentIntent(models.Model):
    """
    Track Stripe payment intents and webhooks
    """
    INTENT_STATUS = [
        ('requires_payment_method', 'Requires Payment Method'),
        ('requires_confirmation', 'Requires Confirmation'),
        ('requires_action', 'Requires Action'),
        ('processing', 'Processing'),
        ('requires_capture', 'Requires Capture'),
        ('canceled', 'Canceled'),
        ('succeeded', 'Succeeded'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    stripe_payment_intent_id = models.CharField(max_length=200, unique=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment_intents')
    
    amount = models.PositiveIntegerField()  # Amount in cents
    currency = models.CharField(max_length=3, default='nok')
    status = models.CharField(max_length=30, choices=INTENT_STATUS)
    
    # Payment method details
    payment_method_type = models.CharField(max_length=50, blank=True)
    last_four = models.CharField(max_length=4, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Raw webhook data
    webhook_data = models.JSONField(default=dict, blank=True)
    
    class Meta:
        db_table = 'core_payment_intent'
        verbose_name = 'Payment Intent'
        verbose_name_plural = 'Payment Intents'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['stripe_payment_intent_id']),
            models.Index(fields=['order']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Payment Intent {self.stripe_payment_intent_id} - {self.order.order_number}"
