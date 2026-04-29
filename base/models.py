from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
from datetime import timedelta
import uuid


class InvestmentPlan(models.Model):
    """Investment plan tiers (Basic, Standard, Professional)"""

    class PlanType(models.TextChoices):
        BASIC = 'basic', 'Basic'
        STANDARD = 'standard', 'Standard'
        PROFESSIONAL = 'professional', 'Professional'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=20, choices=PlanType.choices, unique=True)
    slug = models.SlugField(unique=True)

    # Investment ranges (in NGN)
    min_amount = models.DecimalField(max_digits=15, decimal_places=2)
    max_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True,
                                     help_text="Null means no upper limit")

    # Duration in months
    duration_months = models.PositiveIntegerField()

    # Payout structure
    payout_frequency_months = models.PositiveIntegerField(
        help_text="Months between payouts (e.g., 4 for every 4 months or 3 for every 3 months)"
    )
    total_payouts = models.PositiveIntegerField(
        help_text="Total number of payouts over the duration"
    )

    # Returns
    roi_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Annual ROI percentage"
    )
    is_annual_roi = models.BooleanField(
        default=False,
        help_text="Is the ROI calculated annually?"
    )

    # Display
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['display_order', 'min_amount']
        verbose_name = 'Investment Plan'
        verbose_name_plural = 'Investment Plans'

    def __str__(self):
        max_display = '∞' if not self.max_amount else f"{self.max_amount:,.0f}"
        return f"{self.get_name_display()} (₦{self.min_amount:,.0f} - ₦{max_display})"

    @property
    def investment_range_display(self):
        """Formatted investment range like '₦500K - ₦5M'"""
        min_str = self._format_amount(self.min_amount)
        if self.max_amount:
            max_str = self._format_amount(self.max_amount)
            return f"{min_str} - {max_str}"
        return f"{min_str}+"

    @property
    def payout_structure_display(self):
        """Formatted payout structure like '3 payouts (every 4 months)'"""
        return f"{self.total_payouts} payouts (every {self.payout_frequency_months} months)"

    @property
    def returns_display(self):
        """Formatted returns like '15% ROI' or '30% Annual ROI'"""
        if self.is_annual_roi:
            return f"{self.roi_percentage:.0f}% Annual ROI"
        return f"{self.roi_percentage:.0f}% ROI"

    @property
    def duration_display(self):
        """Formatted duration like '12 Months'"""
        return f"{self.duration_months} Months"

    def _format_amount(self, amount):
        """Convert amount to K/M format"""
        if amount >= 1000000:
            return f"₦{amount/1000000:.0f}M"
        elif amount >= 1000:
            return f"₦{amount/1000:.0f}K"
        return f"₦{amount:.0f}"

    def calculate_total_return(self, investment_amount):
        """Calculate total return for a given investment amount"""
        # Ensure all values are Decimal
        amount = Decimal(str(investment_amount))
        roi = Decimal(str(self.roi_percentage))

        if self.is_annual_roi:
            years = Decimal(self.duration_months) / Decimal(12)
            return amount * (roi / Decimal(100)) * years
        else:
            return amount * (roi / Decimal(100))

    def calculate_payout_amount(self, investment_amount):
        """Calculate each individual payout amount"""
        total_return = self.calculate_total_return(investment_amount)
        principal_per_payout = investment_amount / self.total_payouts
        return_per_payout = total_return / self.total_payouts
        return principal_per_payout + return_per_payout
    
    # @property
    # def duration_days(self):
    #     """Human-readable duration"""
    #     if self.duration_days >= 365:
    #         years = self.duration_days // 365
    #         return f"{years} year{'s' if years > 1 else ''}"
    #     elif self.duration_days >= 30:
    #         months = self.duration_days // 30
    #         return f"{months} month{'s' if months > 1 else ''}"
    #     elif self.duration_days >= 7:
    #         weeks = self.duration_days // 7
    #         return f"{weeks} week{'s' if weeks > 1 else ''}"
    #     return f"{self.duration_days} day{'s' if self.duration_days > 1 else ''}"
    
    @property
    def roi_amount(self):
        """Calculate ROI on minimum amount for display"""
        return self.min_amount * (self.roi_percentage / 100)
    
    # def get_name_display(self):
    #     return self.get_name_display or self.name


class InvestmentStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Approval'
    ACTIVE = 'active', 'Active'
    PAYOUT_SCHEDULED = 'payout_scheduled', 'Payout Scheduled'
    PAYOUT_COMPLETED = 'payout_completed', 'Payout Completed'
    COMPLETED = 'completed', 'Completed'
    CANCELLED = 'cancelled', 'Cancelled'


class Investment(models.Model):
    """User investments in specific plans"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='investments'
    )
    plan = models.ForeignKey(
        InvestmentPlan,
        on_delete=models.PROTECT,
        related_name='investments'
    )

    # Investment details
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    reference_code = models.CharField(max_length=50, unique=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=InvestmentStatus.choices,
        default=InvestmentStatus.PENDING
    )

    # Dates
    investment_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    maturity_date = models.DateTimeField(null=True, blank=True)

    # Payout tracking
    total_expected_return = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_paid_out = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    payouts_completed = models.PositiveIntegerField(default=0)

    # Payment proof
    payment_proof = models.FileField(
        upload_to='investments/payment_proofs/%Y/%m/',
        blank=True,
        null=True
    )
    payment_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verified_investments'
    )
    payment_verified_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'maturity_date']),
        ]

    def __str__(self):
        return f"{self.user} - {self.plan} - ₦{self.amount:,.2f}"

    def save(self, *args, **kwargs):
        if not self.reference_code:
            self.reference_code = f"INV-{self.plan.name.upper()}-{uuid.uuid4().hex[:8].upper()}"

        if self.status == InvestmentStatus.ACTIVE and not self.start_date:
            self.start_date = timezone.now() + timedelta(days=31 *
                                                         self.plan.payout_frequency_months)
            # Calculate maturity date
            self.maturity_date = self.start_date + timezone.timedelta(
                days=self.plan.duration_months * 31
            )
            # Calculate expected return
            self.total_expected_return = self.plan.calculate_total_return(
                self.amount)
            
             

        # if self.status == InvestmentStatus.ACTIVE:
        #     self.total_paid_out = (self.total_expected_return/self.plan.total_payouts) * self.payouts_completed

        super().save(*args, **kwargs)

    @property
    def next_payout_date(self):
        """Calculate next payout date"""
        if self.status != InvestmentStatus.ACTIVE:
            return None

        if self.payouts_completed >= self.plan.total_payouts:
            return None

        # Calculate based on start date and payout frequency
        months_passed = self.payouts_completed * self.plan.payout_frequency_months
        next_payout = self.start_date + \
            timezone.timedelta(days=months_passed * 31)
        
        return next_payout

    @property
    def progress_percentage(self):
        """Investment progress percentage"""
        if self.payouts_completed == 0:
            return 0
        return (self.payouts_completed / self.plan.total_payouts) * 100


class InvestmentPayout(models.Model):
    """Individual payout records for investments"""

    class PayoutStatus(models.TextChoices):
        SCHEDULED = 'scheduled', 'Scheduled'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    investment = models.ForeignKey(
        Investment,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    payout_number = models.PositiveIntegerField()  # 1st, 2nd, 3rd payout, etc.

    # Amounts
    principal_amount = models.DecimalField(max_digits=15, decimal_places=2)
    return_amount = models.DecimalField(max_digits=15, decimal_places=2)
    total_amount = models.DecimalField(max_digits=15, decimal_places=2)

    # Schedule
    scheduled_date = models.DateTimeField()
    processed_date = models.DateTimeField(null=True, blank=True)

    # Status
    status = models.CharField(
        max_length=20,
        choices=PayoutStatus.choices,
        default=PayoutStatus.SCHEDULED
    )

    # Payment details
    payment_method = models.CharField(max_length=50, blank=True)
    payment_reference = models.CharField(max_length=100, blank=True)
    receipt = models.FileField(
        upload_to='investments/payout_receipts/%Y/%m/',
        blank=True,
        null=True
    )

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['investment', 'payout_number']
        unique_together = ['investment', 'payout_number']

    def __str__(self):
        return f"{self.investment.reference_code} - Payout #{self.payout_number}"

    def save(self, *args, **kwargs):
        self.total_amount = self.principal_amount + self.return_amount
        super().save(*args, **kwargs)
