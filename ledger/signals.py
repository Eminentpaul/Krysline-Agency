from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import FinancialEntry, Expense
from affiliation.models import Affiliate, PropertyTransaction, AffiliatePackage
from users.models import Withdrawal, Notification, Transaction
from base.models import Investment, InvestmentPayout, InvestmentStatus


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
        # if not FinancialEntry.objects.filter(reference_id=ref).exists():
        FinancialEntry.objects.create(
            actor=instance.user,
            entry_type='inflow',
            category='package',
            amount=instance.package.price,
            description=f"Revenue from {instance.package.name} package purchase by {instance.user.get_full_name()}",
            reference_id=ref
        )


@receiver(post_save, sender=Investment)
def track_investment_inflow(sender, instance, created, **kwargs):
    """
    AUTOMATIC INFLOW: Triggers when an Investment is activated 
    after paying for a Investment.
    """
    if instance.status == InvestmentStatus.ACTIVE:
        ref = f"INVEST-{str(instance.user.username).capitalize()}-{instance.plan.name}"
        with transaction.atomic():
            FinancialEntry.objects.create(
                actor=instance.user,
                entry_type='inflow',
                category='investment',
                amount=instance.amount,
                description=f"Investment from {instance.plan.name} Invested by {instance.user.get_full_name()}",
                reference_id=ref
            )

            # Create Transaction
            Transaction.objects.create(
                    user=instance.user,
                    amount=instance.amount,
                    transaction_type='investment',
                    description=f"Investment for {instance.plan.name})"
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




@receiver(post_save, sender=FinancialEntry)
def create_notification(sender, instance, created, **kwargs):
    if created:
        note = Notification()
        if instance.category == 'referral':
            note.create_notification(
                user=instance.actor,
                title=f"Commission from your Referral",
                message=f"You received ₦{instance.amount} commission from your Referral",
                notification_type=Notification.NotificationType.REFERRAL,
                priority=Notification.Priority.NORMAL,
            )
        elif instance.category == 'package':
            package = AffiliatePackage.objects.filter(price=instance.amount).first()
            note.create_notification(
                user=instance.actor,
                title=f"Package Subscription",
                message=f"Your Subscription of ₦{instance.amount} to a {package.name} Package: {package.get_name_display()}",
                notification_type=Notification.NotificationType.PACKAGE,
                priority=Notification.Priority.NORMAL,
            )
        elif instance.category == 'commission':
            note.create_notification(
                user=instance.actor,
                title="Commission Withdrawal",
                message=f"Your Withdrawl of ₦{instance.amount} has been approved and Paid",
                notification_type=Notification.NotificationType.COMMISSION,
                priority=Notification.Priority.NORMAL,
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
                category=instance.category if instance.category in dict(
                    FinancialEntry.CATEGORIES) else 'other',
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
                actor=instance.affiliate.user,  # The agent who made the sale
                entry_type='inflow',
                category='property_sale',  # Add this to CATEGORIES in your model
                amount=instance.amount,
                description=f"Property {instance.transaction_type}: {instance.transaction_id} by {instance.affiliate.user.get_full_name()}",
                reference_id=ref
            )
