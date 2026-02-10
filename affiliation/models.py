from django.db import models
from django.db import models, transaction
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
from decimal import Decimal
import hashlib, secrets, string
from authentication.models import UserProfile
# from datetime import timezone
from django.utils import timezone
from auditlog.registry import auditlog



class AffiliatePackage(models.Model):
    """
    Registration packages (₦25k, ₦50k, ₦100k, ₦200k, ₦500k).
    """
    PACKAGE_CHOICES = [
        ('BASIC', '₦25,000 - 1 Generation'),
        ('STANDARD', '₦50,000 - 2 Generations'),
        ('PREMIUM', '₦100,000 - 2 Generations'),
        ('PROFESSIONAL', '₦200,000 - 3 Generations'),
        ('ELITE', '₦500,000 - 3 Generations + Spillover'),
    ]

    name = models.CharField(max_length=50, choices=PACKAGE_CHOICES, unique=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    generations = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(3)])
    
    # Store percentages like: {"1": 20.0, "2": 10.0, "3": 5.0}
    commissions = models.JSONField(default=dict, help_text="Format: {'1': 20, '2': 10}")
    
    has_spillover = models.BooleanField(default=False)
    url = models.URLField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.get_name_display()} (₦{self.price:,.2f})"
    


class CommissionLog(models.Model):
    """
    Secure audit trail of every Naira paid out.
    """
    recipient_profile = models.ForeignKey('authentication.UserProfile', on_delete=models.PROTECT, related_name='earnings')
    source_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    generation = models.IntegerField()
    
    # Security: Digital Seal to prevent database manipulation
    integrity_hash = models.CharField(max_length=64, editable=False)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Create a SHA-256 hash of the transaction data
        # If the amount or recipient is changed in the DB, the hash won't match
        hash_data = f"{self.recipient_profile_id}{self.amount}{self.generation}{settings.SECRET_KEY}"
        self.integrity_hash = hashlib.sha256(hash_data.encode()).hexdigest()
        super().save(*args, **kwargs)

    def is_valid(self):
        """Verify that the record hasn't been tampered with."""
        expected_hash = hashlib.sha256(
            f"{self.recipient_profile_id}{self.amount}{self.generation}{settings.SECRET_KEY}".encode()
        ).hexdigest()
        return self.integrity_hash == expected_hash

# Register for auditlog tracking
auditlog.register(AffiliatePackage)
auditlog.register(CommissionLog)



class Affiliate(models.Model):
    """
    Handles the business side of KAL: Referrals, Packages, and Uplines.
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='affiliate_record'
    )
    
    # The MLM Tree: Points to another Affiliate (their boss/referrer)
    upline = models.ForeignKey(
        'self', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='downline_team'
    )
    
    # Link to the ₦25k, ₦50k, ₦100k, etc. packages
    package = models.ForeignKey(
        'AffiliatePackage', 
        on_delete=models.PROTECT, 
        related_name='members'
    )

    referral_code = models.CharField(max_length=15, unique=True, db_index=True)
    is_active = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Generate a secure, unique KAL referral code if it doesn't exist
        if not self.referral_code:
            alphabet = string.ascii_uppercase + string.digits
            while True:
                code = 'KAL-' + ''.join(secrets.choice(alphabet) for _ in range(6))
                if not Affiliate.objects.filter(referral_code=code).exists():
                    self.referral_code = code
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} ({self.referral_code})"
    

    


class PropertyTransaction(models.Model):
    """
    Records actual property sales/services. 
    Commissions are ONLY triggered when 'is_verified' is True.
    """
    TRANSACTION_TYPES = [
        ('SALE', 'Property Sale'),
        ('RENT', 'Property Rent'),
        ('SERVICE', 'Service Fee'),
    ]

    transaction_id = models.CharField(max_length=100, unique=True, editable=False)
    affiliate = models.ForeignKey('Affiliate', on_delete=models.PROTECT, related_name='sales')
    
    # Financial Details
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    description = models.TextField()
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES, default='SALE')

    # Security & Verification
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    verification_date = models.DateTimeField(null=True, blank=True)
    
    # Data Integrity Hash (To prevent database tampering)
    tx_hash = models.CharField(max_length=64, editable=False, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # 1. Generate a unique ID if it doesn't exist
        if not self.transaction_id:
            import uuid
            self.transaction_id = f"KAL-TX-{uuid.uuid4().hex[:8].upper()}"

        # 2. Create a Digital Signature (Hash) of the transaction
        # If the amount or affiliate changes later, the hash won't match
        hash_string = f"{self.transaction_id}{self.amount}{self.affiliate_id}{settings.SECRET_KEY}"
        self.tx_hash = hashlib.sha256(hash_string.encode()).hexdigest()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_id} - ₦{self.amount}"

    class Meta:
        verbose_name = "Property Transaction"
        ordering = ['-created_at']