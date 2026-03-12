import hashlib
from django.db import models
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError

class TransactionPIN(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='transaction_pin'
    )
    # Store as a hash, not 1234!
    pin_hash = models.CharField(max_length=128) 
    
    # Security Tracking
    failed_attempts = models.IntegerField(default=0)
    last_attempt = models.DateTimeField(auto_now=True)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_pin(self, raw_pin):
        """Hashes the 4 or 6 digit PIN before saving."""
        if not str(raw_pin).isdigit() or len(str(raw_pin)) not in [4, 6]:
            raise ValidationError("PIN must be 4 or 6 digits.")
        self.pin_hash = make_password(raw_pin)
        self.save()

    def unblock_pin(self):        
        if self.is_locked == True:
            self.is_locked = False
            self.failed_attempts = 0
            self.save()

    def check_pin(self, raw_pin):
        """Verifies the PIN and handles lockout logic."""
        if self.is_locked:
            return False
        
        is_correct = check_password(raw_pin, self.pin_hash)
        
        if is_correct:
            self.failed_attempts = 0
            self.save()
            return True
        else:
            self.failed_attempts += 1
            if self.failed_attempts >= 5: # Lock after 5 tries
                self.is_locked = True
            self.save()
            return False

    def __str__(self):
        return f"PIN for {self.user.get_full_name()}"
