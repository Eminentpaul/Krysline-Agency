from django.db import models, transaction
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from cryptography.fernet import Fernet
from decimal import Decimal
import hashlib, secrets, string

# Create your models here.
# 1.1 Secure Encryption Field
class EncryptedField(models.Field):
    """AES-256 encryption for database values."""
    def __init__(self, *args, **kwargs):
        kwargs['max_length'] = 500  # Extra space for encrypted overhead
        super().__init__(*args, **kwargs)

    def _get_fernet(self):
        return Fernet(settings.ENCRYPTION_KEY)

    def get_prep_value(self, value):
        if value is None: return value
        return 'enc:' + self._get_fernet().encrypt(str(value).encode()).decode()

    def from_db_value(self, value, expression, connection):
        if value is None or not value.startswith('enc:'): return value
        return self._get_fernet().decrypt(value[4:].encode()).decode()
    



class SecurityAuditLog(models.Model):
    """Comprehensive security audit logging"""
    ACTION_CHOICES = [
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('REGISTER', 'User Registration'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('COMMISSION_CREATE', 'Commission Created'),
        ('COMMISSION_PAY', 'Commission Paid'),
        ('TRANSACTION_CREATE', 'Transaction Created'),
        ('PROFILE_UPDATE', 'Profile Update'),
        ('SUSPICIOUS', 'Suspicious Activity'),
        ('API_ACCESS', 'API Access'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    details = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)
    severity = models.CharField(max_length=20, choices=[
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ], default='LOW')
    
    class Meta:
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['severity', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user} - {self.action} - {self.timestamp}"
