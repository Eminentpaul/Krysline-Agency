from django.db import models
from django.db import models, transaction
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
from decimal import Decimal
import hashlib, secrets, string
from authentication.models import UserProfile



# Create your models here.
class AffiliatePackage(models.Model):
    name = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    generations = models.IntegerField()  # 1, 2, or 3
    # Percentages [Gen1, Gen2, Gen3]
    commissions = models.JSONField(default=dict) 

class CommissionLog(models.Model):
    recipient = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    source_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    generation = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)



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
    is_active = models.BooleanField(default=True)
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