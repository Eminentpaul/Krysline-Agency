from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import transaction
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
from decimal import Decimal
import hashlib, secrets, string
from security.models import EncryptedField

# Create your models here.
class User(AbstractUser):

    USER_TYPE = (
        ('affiliate', 'affiliate'),
        ('admin', 'admin')
    )
    first_name = models.CharField(max_length=250)
    last_name = models.CharField(max_length=250)
    username = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=25, choices=USER_TYPE, default='affiliate')
    is_active = models.BooleanField(default=False)
    verified_email = models.BooleanField(default=False)


    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']
    USERNAME_FIELD = 'email'


    def __str__(self):
        return self.first_name
    



# 1.2 The MLM Hierarchy & Security Profile
class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    # Use string reference to prevent circular imports
    referrer = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='downline')
    
    # Financials
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    # bvn = EncryptedField(null=True, blank=True)
    
    # Security State
    two_factor_enabled = models.BooleanField(default=False)
    account_locked_until = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    last_login_ip_address = models.GenericIPAddressField(unique=True, null=True, blank=True, db_index=True)

    def clean(self):
        # Recursive prevention
        if self.referrer == self:
            raise ValidationError("You cannot refer yourself.")






class BlacklistedIP(models.Model):
    ip_address = models.GenericIPAddressField(unique=True, db_index=True)
    reason = models.CharField(max_length=255, default="Brute force protection")
    blocked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Blocked: {self.ip_address}"