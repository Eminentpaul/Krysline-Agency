from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from .models import Withdrawal, Transaction
from affiliation.models import Affiliate

@receiver(post_save, sender=Withdrawal)
def create_withdrawal_transaction(sender, instance, created, **kwargs):
    """
    Triggers ONLY when an admin changes status to 'approved'.
    """
    # 1. Check if it's approved
    if instance.status == 'approved':
        # 2. Check if we ALREADY recorded this to prevent double-entry
        already_recorded = Transaction.objects.filter(
            user=instance.user,
            transaction_type='withdrawal',
            description__contains=f"Ref: {instance.transaction_id}"
        ).exists()

        if not already_recorded:
            with transaction.atomic():
                # Create the Ledger entry
                Transaction.objects.create(
                    user=instance.user,
                    amount=instance.amount,
                    transaction_type='withdrawal',
                    description=f"Withdrawal Approved (Ref: {instance.transaction_id})"
                )
                # Note: We don't need 'instance.transaction = new_transaction' 
                # unless you add a ForeignKey to your Withdrawal model.

@receiver(post_save, sender=Affiliate)
def record_package_purchase(sender, instance, created, **kwargs):
    """
    Records a transaction when an Affiliate is activated.
    """
    # Only record if the affiliate is ACTIVE and has a package
    if instance.is_active and instance.package:
        already_recorded = Transaction.objects.filter(
            user=instance.user, 
            transaction_type='package_purchase'
        ).exists()

        if not already_recorded:
            Transaction.objects.create(
                user=instance.user,
                amount=instance.package.price,
                transaction_type='package_purchase',
                description=f"Payment for {instance.package.name} Package"
            )