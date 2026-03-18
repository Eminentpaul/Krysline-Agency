import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone


class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('package_purchase', 'Package Purchase'),
        ('commission', 'Commission Earned'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(
        max_length=50, choices=TRANSACTION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.transaction_type} - ₦{self.amount}"


class Withdrawal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved & Paid'),
        ('rejected', 'Rejected'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    transaction_id = models.CharField(
        max_length=100, unique=True, editable=False)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[
                                 MinValueValidator(Decimal('100'))])
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import secrets
            self.transaction_id = f"WTH-{secrets.token_hex(6).upper()}"
        super().save(*args, **kwargs)


class Notification(models.Model):
    """
    User Notification model for storing and managing user notifications.
    Supports multiple notification types, read status, and automatic expiration.
    """

    # Notification Types
    class NotificationType(models.TextChoices):
        INFO = 'info', 'Information'
        SUCCESS = 'success', 'Success'
        WARNING = 'warning', 'Warning'
        ERROR = 'error', 'Error'
        PACKAGE = 'package', 'Package Update'
        PAYMENT = 'payment', 'Payment'
        COMMISSION = 'commission', 'Commission'
        REFERRAL = 'referral', 'Referral'
        SYSTEM = 'system', 'System'

    # Priority Levels
    class Priority(models.IntegerChoices):
        LOW = 1, 'Low'
        NORMAL = 2, 'Normal'
        HIGH = 3, 'High'
        URGENT = 4, 'Urgent'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        help_text="Recipient user"
    )
    title = models.CharField(
        max_length=255,
        help_text="Notification headline"
    )
    message = models.TextField(
        help_text="Detailed notification message"
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType.choices,
        default=NotificationType.INFO
    )
    priority = models.IntegerField(
        choices=Priority.choices,
        default=Priority.NORMAL
    )
    is_read = models.BooleanField(
        default=False,
        help_text="Whether user has read this notification"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read', '-created_at']),
            models.Index(fields=['user', 'notification_type']),
            # models.Index(fields=['is_active', 'expires_at']),
        ]
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"{self.user} - {self.title[:50]} ({self.get_notification_type_display()})"

    def mark_as_read(self):
        """Mark notification as read with timestamp."""
        if not self.is_read:
            self.is_read = True
            # self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'updated_at'])

    def mark_as_unread(self):
        """Mark notification as unread."""
        if self.is_read:
            self.is_read = False
            # self.read_at = None
            self.save(update_fields=['is_read', 'read_at', 'updated_at'])

    @property
    def time_since_created(self):
        """Human-readable time since creation."""
        from django.contrib.humanize.templatetags.humanize import naturaltime
        return naturaltime(self.created_at)

    @classmethod
    def create_notification(cls, user, title, message, **kwargs):
        """
        Factory method to create notifications easily.

        Usage:
        Notification.create_notification(
            user=request.user,
            title="Payment Received",
            message="Your payment of ₦5000 was successful",
            notification_type=Notification.NotificationType.PAYMENT,
            priority=Notification.Priority.HIGH,
            action_url="/dashboard/payments/"
        )
        """
        return cls.objects.create(
            user=user,
            title=title,
            message=message,
            **kwargs
        )

    @classmethod
    def get_unread_count(cls, user):
        """Get count of unread notifications for user."""
        return cls.objects.filter(
            user=user,
            is_read=False
        ).count()

    @classmethod
    def mark_all_as_read(cls, user, notification_type=None):
        """Bulk mark notifications as read."""
        queryset = cls.objects.filter(user=user, is_read=False)
        if notification_type:
            queryset = queryset.filter(notification_type=notification_type)

        count = queryset.count()
        queryset.update(is_read=True)
        return count





