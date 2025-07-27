"""
Forms for JuridiskPorten
Custom forms with enhanced validation and security
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from .models import User
from .validators import validate_phone_number


class CustomUserCreationForm(UserCreationForm):
    """
    Enhanced user registration form with additional fields
    """
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email Address'
        })
    )
    phone = forms.CharField(
        max_length=15,
        required=False,
        validators=[validate_phone_number],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone Number (optional)'
        })
    )
    organization = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Organization (optional)'
        })
    )
    gdpr_consent = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='I agree to the processing of my personal data in accordance with GDPR'
    )
    accepts_marketing = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label='I would like to receive marketing communications'
    )
    
    class Meta:
        model = User
        fields = (
            'username', 'first_name', 'last_name', 'email', 
            'phone', 'organization', 'password1', 'password2',
            'gdpr_consent', 'accepts_marketing'
        )
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Style password fields
        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })
        
        # Update help texts
        self.fields['username'].help_text = 'Choose a unique username (letters, digits and @/./+/-/_ only)'
        self.fields['password1'].help_text = (
            'Your password must contain at least 12 characters including '
            'uppercase and lowercase letters, numbers, and special characters.'
        )
    
    def clean_email(self):
        """Ensure email is unique"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with this email already exists.')
        return email
    
    def save(self, commit=True):
        """Save user with additional fields"""
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data['phone']
        user.organization = self.cleaned_data['organization']
        user.gdpr_consent = self.cleaned_data['gdpr_consent']
        user.accepts_marketing = self.cleaned_data['accepts_marketing']
        
        if self.cleaned_data['gdpr_consent']:
            from django.utils import timezone
            user.gdpr_consent_date = timezone.now()
        
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """
    User profile editing form
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'phone', 
            'organization', 'accepts_marketing'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email Address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Phone Number'
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Organization'
            }),
            'accepts_marketing': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'accepts_marketing': 'Receive marketing communications',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add validators
        self.fields['phone'].validators = [validate_phone_number]
        
        # Make email field readonly if user is verified
        if self.instance and self.instance.is_verified:
            self.fields['email'].widget.attrs['readonly'] = True
            self.fields['email'].help_text = 'Contact support to change your verified email address.'
    
    def clean_email(self):
        """Prevent changing verified email"""
        email = self.cleaned_data.get('email')
        if self.instance and self.instance.is_verified:
            if email != self.instance.email:
                raise ValidationError('Cannot change verified email address.')
        
        # Check uniqueness for other users
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError('A user with this email already exists.')
        
        return email


class ContactForm(forms.Form):
    """
    General contact form for support inquiries
    """
    INQUIRY_TYPES = [
        ('general', 'General Inquiry'),
        ('technical', 'Technical Support'),
        ('billing', 'Billing Question'),
        ('content', 'Content Request'),
        ('legal', 'Legal Consultation'),
    ]
    
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email'
        })
    )
    inquiry_type = forms.ChoiceField(
        choices=INQUIRY_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    package_related = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False,
        empty_label="Not package-specific",
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Related Package'
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Your message...'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set package queryset
        from .models import LegalPackage
        self.fields['package_related'].queryset = LegalPackage.objects.filter(
            is_active=True
        ).order_by('sort_order')


class ContentSearchForm(forms.Form):
    """
    Search form for content within packages
    """
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search content...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=None,  # Set in __init__
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    content_type = forms.ChoiceField(
        choices=[
            ('', 'All Types'),
            ('article', 'Articles'),
            ('form', 'Forms & Templates'),
            ('qa', 'Q&A'),
            ('resource', 'Resources'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    def __init__(self, package=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if package:
            from .models import ContentCategory
            self.fields['category'].queryset = ContentCategory.objects.filter(
                is_active=True
            ).order_by('sort_order')


# ==============================================================================
# PHASE 3: E-COMMERCE FORMS
# ==============================================================================

class CheckoutForm(forms.Form):
    """
    Checkout form for order billing information
    """
    billing_name = forms.CharField(
        max_length=200,
        required=True,
        label='Navn',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Fullt navn'
        })
    )
    
    billing_email = forms.EmailField(
        required=True,
        label='E-post',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'din@epost.no'
        })
    )
    
    billing_organization = forms.CharField(
        max_length=200,
        required=False,
        label='Organisasjon (valgfritt)',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Firmanavn eller organisasjon'
        })
    )
    
    billing_address = forms.CharField(
        required=False,
        label='Adresse (valgfritt)',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Gateadresse, postnummer, poststed'
        })
    )
    
    billing_city = forms.CharField(
        max_length=100,
        required=False,
        label='By',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'By'
        })
    )
    
    billing_postal_code = forms.CharField(
        max_length=20,
        required=False,
        label='Postnummer',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '0000'
        })
    )
    
    customer_notes = forms.CharField(
        required=False,
        label='Notater til bestilling (valgfritt)',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Eventuelle spesielle ønsker eller kommentarer'
        })
    )
    
    terms_accepted = forms.BooleanField(
        required=True,
        label='Jeg godtar vilkårene',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    marketing_consent = forms.BooleanField(
        required=False,
        label='Jeg ønsker å motta markedsføring via e-post',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    def clean_billing_email(self):
        """Validate billing email"""
        email = self.cleaned_data.get('billing_email')
        if email:
            email = email.lower().strip()
        return email
    
    def clean_billing_postal_code(self):
        """Validate Norwegian postal code format"""
        postal_code = self.cleaned_data.get('billing_postal_code')
        if postal_code:
            postal_code = postal_code.strip()
            if len(postal_code) == 4 and postal_code.isdigit():
                return postal_code
            elif len(postal_code) == 0:
                return ''
            else:
                raise ValidationError('Postnummer må være 4 siffer.')
        return postal_code


class CouponForm(forms.Form):
    """
    Form for applying coupon codes
    """
    coupon_code = forms.CharField(
        max_length=50,
        required=True,
        label='Kupongkode',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Skriv inn kupongkode',
            'style': 'text-transform: uppercase;'
        })
    )
    
    def clean_coupon_code(self):
        """Clean and validate coupon code"""
        code = self.cleaned_data.get('coupon_code')
        if code:
            code = code.strip().upper()
            if len(code) < 3:
                raise ValidationError('Kupongkode må være minst 3 tegn.')
        return code


class BulkCouponForm(forms.Form):
    """
    Admin form for creating multiple coupons
    """
    COUPON_TYPE_CHOICES = [
        ('percentage', 'Prosent rabatt'),
        ('fixed', 'Fast beløp'),
    ]
    
    name_prefix = forms.CharField(
        max_length=100,
        required=True,
        label='Navn-prefiks',
        help_text='Brukes som base for kupongnavnene',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'f.eks. "Julegave 2025"'
        })
    )
    
    code_prefix = forms.CharField(
        max_length=20,
        required=True,
        label='Kode-prefiks',
        help_text='Brukes som base for kupongkodene',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'f.eks. "XMAS25"'
        })
    )
    
    quantity = forms.IntegerField(
        min_value=1,
        max_value=1000,
        required=True,
        label='Antall kuponger',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10'
        })
    )
    
    coupon_type = forms.ChoiceField(
        choices=COUPON_TYPE_CHOICES,
        required=True,
        label='Rabatttype',
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    discount_value = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=True,
        label='Rabattverdi',
        help_text='Prosent (uten %-tegn) eller fast beløp i kr',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '10.00'
        })
    )
    
    minimum_order_amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        label='Minimumsbeløp',
        help_text='Minimumsbestilling for å bruke kupongen',
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '0.00'
        })
    )
    
    usage_limit_per_user = forms.IntegerField(
        min_value=1,
        required=True,
        initial=1,
        label='Bruksgrense per bruker',
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )
    
    valid_days = forms.IntegerField(
        min_value=1,
        max_value=365,
        required=True,
        initial=30,
        label='Gyldig i antall dager',
        help_text='Fra i dag',
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )
    
    def clean_code_prefix(self):
        """Clean and validate code prefix"""
        prefix = self.cleaned_data.get('code_prefix')
        if prefix:
            prefix = prefix.strip().upper()
            # Remove special characters except dash and underscore
            import re
            prefix = re.sub(r'[^A-Z0-9\-_]', '', prefix)
        return prefix
