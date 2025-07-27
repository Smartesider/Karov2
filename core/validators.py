"""
Custom validators for JuridiskPorten
Password validation and other security validators
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import re


class CustomPasswordValidator:
    """
    Enhanced password validator for JuridiskPorten
    Requires strong passwords with multiple character types
    """
    
    def validate(self, password, user=None):
        """
        Validate the password against security requirements
        """
        errors = []
        
        # Check minimum length (already handled by MinimumLengthValidator)
        if len(password) < 12:
            errors.append(_("Password must be at least 12 characters long."))
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append(_("Password must contain at least one uppercase letter."))
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            errors.append(_("Password must contain at least one lowercase letter."))
        
        # Check for digit
        if not re.search(r'\d', password):
            errors.append(_("Password must contain at least one digit."))
        
        # Check for special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append(_("Password must contain at least one special character."))
        
        # Check for common patterns
        if re.search(r'(.)\1{2,}', password):
            errors.append(_("Password cannot contain three or more consecutive identical characters."))
        
        # Check for sequential characters
        if self._has_sequential_chars(password):
            errors.append(_("Password cannot contain sequential characters (e.g., 123, abc)."))
        
        # Check against user information if available
        if user:
            user_words = []
            if user.first_name:
                user_words.append(user.first_name.lower())
            if user.last_name:
                user_words.append(user.last_name.lower())
            if user.email:
                user_words.append(user.email.split('@')[0].lower())
            if user.organization:
                user_words.append(user.organization.lower())
            
            for word in user_words:
                if len(word) > 3 and word in password.lower():
                    errors.append(_("Password cannot contain personal information."))
                    break
        
        if errors:
            raise ValidationError(errors)
    
    def _has_sequential_chars(self, password):
        """
        Check for sequential characters in password
        """
        password_lower = password.lower()
        
        # Check for sequential letters
        for i in range(len(password_lower) - 2):
            if (ord(password_lower[i+1]) == ord(password_lower[i]) + 1 and
                ord(password_lower[i+2]) == ord(password_lower[i]) + 2):
                return True
        
        # Check for sequential numbers
        for i in range(len(password) - 2):
            if (password[i:i+3].isdigit() and
                int(password[i+1]) == int(password[i]) + 1 and
                int(password[i+2]) == int(password[i]) + 2):
                return True
        
        return False
    
    def get_help_text(self):
        return _(
            "Your password must contain at least 12 characters including "
            "uppercase and lowercase letters, numbers, and special characters. "
            "It cannot contain sequential characters or personal information."
        )


def validate_phone_number(value):
    """
    Validate Norwegian phone numbers
    """
    if not value:
        return
    
    # Remove spaces and common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', value)
    
    # Norwegian phone number patterns
    patterns = [
        r'^\+47[2-9]\d{7}$',  # +47 followed by 8 digits starting with 2-9
        r'^47[2-9]\d{7}$',    # 47 followed by 8 digits starting with 2-9
        r'^[2-9]\d{7}$',      # 8 digits starting with 2-9
    ]
    
    if not any(re.match(pattern, cleaned) for pattern in patterns):
        raise ValidationError(
            _('Please enter a valid Norwegian phone number.')
        )


def validate_organization_number(value):
    """
    Validate Norwegian organization numbers (9 digits)
    """
    if not value:
        return
    
    # Remove spaces
    cleaned = re.sub(r'\s', '', value)
    
    if not re.match(r'^\d{9}$', cleaned):
        raise ValidationError(
            _('Organization number must be exactly 9 digits.')
        )
    
    # Validate check digit (simplified version)
    weights = [3, 2, 7, 6, 5, 4, 3, 2]
    sum_weighted = sum(int(cleaned[i]) * weights[i] for i in range(8))
    remainder = sum_weighted % 11
    
    if remainder == 0:
        check_digit = 0
    elif remainder == 1:
        raise ValidationError(_('Invalid organization number.'))
    else:
        check_digit = 11 - remainder
    
    if int(cleaned[8]) != check_digit:
        raise ValidationError(_('Invalid organization number.'))


def validate_file_size(value):
    """
    Validate uploaded file size (max 10MB for documents, 5MB for images)
    """
    if not value:
        return
    
    file_size = value.size
    
    # Get file extension
    file_name = value.name.lower()
    
    # Image files: max 5MB
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if any(file_name.endswith(ext) for ext in image_extensions):
        if file_size > 5 * 1024 * 1024:  # 5MB
            raise ValidationError(_('Image files cannot exceed 5MB.'))
        return
    
    # Document files: max 10MB
    document_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt']
    if any(file_name.endswith(ext) for ext in document_extensions):
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise ValidationError(_('Document files cannot exceed 10MB.'))
        return
    
    # Other files: max 5MB
    if file_size > 5 * 1024 * 1024:  # 5MB
        raise ValidationError(_('Files cannot exceed 5MB.'))


def validate_file_type(value):
    """
    Validate uploaded file types - only allow specific extensions
    """
    if not value:
        return
    
    file_name = value.name.lower()
    
    allowed_extensions = [
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.webp',
        # Documents
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt',
        # Archives (for bulk uploads)
        '.zip', '.rar',
    ]
    
    if not any(file_name.endswith(ext) for ext in allowed_extensions):
        raise ValidationError(
            _('File type not allowed. Allowed types: %(types)s') % {
                'types': ', '.join(allowed_extensions)
            }
        )
