from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import FinancialEntry, Expense
from affiliation.models import Affiliate, PropertyTransaction
from users.models import Withdrawal


@receiver(post_save, sender=Affiliate)
def track_package_inflow(sender, instance, created, **kwargs):
    """
    AUTOMATIC INFLOW: Triggers when an affiliate is activated 
    after paying for a package.
    """
    # Only record if the account just became active
    if instance.is_active and instance.package:
        # Check if we already recorded this to avoid duplicates
        ref = f"PKG-SUB-{str(instance.user.username).capitalize()}-{instance.package.name}"
        if not FinancialEntry.objects.filter(reference_id=ref).exists():
            FinancialEntry.objects.create(
                actor=instance.user,
                entry_type='inflow',
                category='package',
                amount=instance.package.price,
                description=f"Revenue from {instance.package.name} package purchase by {instance.user.get_full_name()}",
                reference_id=ref
            )


@receiver(post_save, sender=Withdrawal)
def track_withdrawal_outflow(sender, instance, created, **kwargs):
    """
    AUTOMATIC OUTFLOW: Triggers when an admin approves 
    a withdrawal request.
    """
    if instance.status == 'approved':
        ref = f"WTH-{instance.transaction_id}"
        if not FinancialEntry.objects.filter(reference_id=ref).exists():
            FinancialEntry.objects.create(
                actor=instance.user,
                entry_type='outflow',
                category='commission',
                amount=instance.amount,
                description=f"Commission payout to {instance.user.get_full_name()}",
                reference_id=ref
            )




@receiver(post_save, sender=Expense)
def track_expense_outflow(sender, instance, created, **kwargs):
    """
    AUTOMATIC OUTFLOW:
    When an expense is approved, record it in FinancialEntry.
    """

    if instance.status == 'approved':
        ref = f"EXP-{instance.receipt_number}"

        if not FinancialEntry.objects.filter(reference_id=ref).exists():
            FinancialEntry.objects.create(
                actor=instance.recorded_by,
                entry_type='outflow',
                category=instance.category if instance.category in dict(FinancialEntry.CATEGORIES) else 'other',
                amount=instance.amount,
                description=f"Expense recorded: {instance.description}",
                reference_id=ref
            )


@receiver(post_save, sender=PropertyTransaction)
def track_property_inflow(sender, instance, created, **kwargs):
    """
    AUTOMATIC INFLOW: Triggers when a property sale is verified.
    Records the total sale amount into the company ledger.
    """
    if instance.is_verified:
        # Create a unique reference for this specific property sale
        ref = f"PROP-{instance.transaction_id}"
        
        # Check for duplicates to maintain 'Eminent' data integrity
        if not FinancialEntry.objects.filter(reference_id=ref).exists():
            FinancialEntry.objects.create(
                actor=instance.affiliate.user, # The agent who made the sale
                entry_type='inflow',
                category='property_sale', # Add this to CATEGORIES in your model
                amount=instance.amount,
                description=f"Property {instance.transaction_type}: {instance.transaction_id} by {instance.affiliate.user.get_full_name()}",
                reference_id=ref
            )