import requests
from monnify.monnify import Monnify
from base64 import b64encode
import base64
import os
from datetime import datetime
from monnify_verification.monnify_api import *
from affiliation.models import Affiliate, AffiliatePackage




data = initiate_transfer(accountNumber="8143122946", bankName="999992-OPay Digital Services Limited (OPay)")

print(data)



from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.conf import settings
import logging
from authentication.models import User

logger = logging.getLogger(__name__)


def payments(request):
    """
    Handle payment verification and activate affiliate subscription.
    Supports both callback redirect (paymentReference) and manual check (user invoice).
    """
    
    # Get reference from callback or user's current invoice
    payment_ref = request.GET.get('paymentReference')
    
    if payment_ref:
        reference = payment_ref
    else:
        try:
            reference = request.user.invoice.inovoice_reference
        except AttributeError:
            messages.error(request, "No pending invoice found.")
            return redirect('choose_package')

    # Verify invoice with Monnify
    invoice_data, is_valid = get_invoice(reference)
    
    if not is_valid or invoice_data.get('invoiceStatus') != 'PAID':
        messages.error(request, "Payment verification failed or payment not completed.")
        return redirect('choose_package')

    # Parse invoice details
    try:
        invoice_ref = invoice_data.get('invoiceReference', '')
        ref_parts = invoice_ref.split('-')
        package_id = int(ref_parts[1]) if len(ref_parts) > 1 else None
    except (IndexError, ValueError, AttributeError) as e:
        logger.error(f"Invalid invoice reference format: {invoice_ref}, Error: {e}")
        messages.error(request, "Invalid invoice reference.")
        return redirect('choose_package')

    amount = float(invoice_data.get('amount', 0))
    customer_email = invoice_data.get('customerEmail', '')
    description = (invoice_data.get('description') or '').lower()

    # Handle subscription payments
    if "subscription" in description:
        return _process_subscription_payment(request, package_id, amount, customer_email, reference)
    
    # Handle other payment types (withdrawals, etc.)
    logger.info(f"Non-subscription payment received: {description}")
    # TODO: Implement withdrawal completion logic here
    messages.info(request, "Payment received. Processing pending.")
    return redirect('dashboard')


def _process_subscription_payment(request, package_id, amount, customer_email, reference):
    """Process successful subscription payment and activate affiliate."""
    
    try:
        with transaction.atomic():
            # Fetch and lock package
            package = get_object_or_404(
                AffiliatePackage, 
                id=package_id, 
                price=amount,
                is_active=True
            )
            
            # Fetch user by email from invoice
            user = get_object_or_404(User, email=customer_email)
            
            duration = settings.DURATION
            
            # Get or create affiliate with row lock
            affiliate, created = Affiliate.objects.select_for_update().get_or_create(
                user=user,
                defaults={
                    'package': package,
                    'duration': duration,
                    'is_active': True,
                    'referral_code': generate_referral_code()  # Ensure this exists
                }
            )
            
            # Handle existing affiliate upgrade/renewal
            if not created:
                # Check if this is an upgrade to higher package
                is_upgrade = (
                    affiliate.package and 
                    affiliate.package.price < package.price
                )
                
                # Check if current subscription is still active
                is_currently_active = (
                    affiliate.is_active and 
                    affiliate.expires_at and 
                    affiliate.expires_at > timezone.now()
                )
                
                if is_currently_active and not is_upgrade:
                    # Already active with same or better package
                    logger.info(f"User {user.id} already has active subscription")
                    messages.info(request, "You already have an active subscription.")
                    return redirect('dashboard')
                
                # Update affiliate with new package
                affiliate.package = package
                affiliate.duration = duration
                affiliate.is_active = True
                
                # Reset expiry date for new subscription
                affiliate.expires_at = timezone.now() + duration
                affiliate.save()

            # Distribute MLM commissions
            commissions_distributed = distribute_commissions(
                new_affiliate=affiliate, 
                new=created
            )
            
            if commissions_distributed:
                # Record successful transaction
                Transaction.objects.create(
                    user=user,
                    amount=package.price,
                    transaction_type='package_purchase',
                    description=f"Subscription: {package.get_name_display()} (Ref: {reference})",
                    status='completed',
                    reference=reference
                )
                
                messages.success(
                    request, 
                    f"Payment successful! {package.get_name_display()} subscription activated."
                )
                return redirect('dashboard')
            else:
                logger.error(f"Commission distribution failed for affiliate {affiliate.id}")
                # Don't fail the payment, but log for manual review
                messages.warning(
                    request, 
                    "Subscription activated. Bonus processing pending."
                )
                return redirect('dashboard')

    except Exception as e:
        logger.exception(f"Subscription processing error: {e}")
        messages.error(request, "Payment verified but activation failed. Contact support.")
        return redirect('choose_package')


def generate_referral_code():
    """Generate unique referral code."""
    import uuid
    import string
    import random
    
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        if not Affiliate.objects.filter(referral_code=code).exists():
            return code