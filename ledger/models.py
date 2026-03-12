from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from auditlog.registry import auditlog

class FinancialEntry(models.Model):
    ENTRY_TYPES = (
        ('inflow', 'Inflow (Revenue/Deposit)'),
        ('outflow', 'Outflow (Expense/Withdrawal)'),
    )
    
    CATEGORIES = (
        ('package', 'Package Purchase'),
        ('commission', 'Commission Payout'),
        ('referral', 'Referral Bonus'),
        ('salary', 'Staff Salary'),
        ('office', 'Office Maintenance'),
        ('utility', 'Utility Bills'),
        ('logistics', 'Logistics/Transport'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
        ('property_sale', 'Property Sale Inflow'),
    )

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='recorded_entries')
    entry_type = models.CharField(max_length=10, choices=ENTRY_TYPES)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    amount = models.DecimalField(max_digits=15, decimal_places=2, validators=[MinValueValidator(0.01)])
    
    # Inventory Link (Optional: Link to specific physical assets if needed)
    description = models.TextField(help_text="Detailed reason for this transaction")
    reference_id = models.CharField(max_length=100, unique=True, help_text="Internal TRX or Receipt Number")
    
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Financial Entries"
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.entry_type.upper()}] {self.category} - ₦{self.amount}"

# Register for deep auditing: This tracks WHO changed WHAT and WHEN
auditlog.register(FinancialEntry)




# import uuid
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone


class Expense(models.Model):

    EXPENSE_CATEGORIES = (
        ('office', 'Office Maintenance'),
        ('utility', 'Utility Bills'),
        ('salary', 'Staff Salary'),
        ('logistics', 'Logistics / Transport'),
        ('marketing', 'Marketing'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='recorded_expenses'
    )

    category = models.CharField(max_length=20, choices=EXPENSE_CATEGORIES)

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)]
    )

    description = models.TextField()

    receipt_number = models.CharField(
        max_length=100,
        unique=True,
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def save(self, *args, **kwargs):
        if not self.receipt_number:
            today = timezone.now().strftime("%Y%m%d")

            last_expense = Expense.objects.filter(
                receipt_number__startswith=f"EXP-{today}"
            ).order_by('-receipt_number').first()

            if last_expense:
                last_number = int(last_expense.receipt_number.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.receipt_number = f"EXP-{today}-{str(new_number).zfill(4)}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.receipt_number} - ₦{self.amount}"