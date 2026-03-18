from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from security.decorators import *
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from affiliation.models import AffiliatePackage, CommissionLog, PropertyTransaction, Affiliate, UserInvoice
from affiliation.services import *
from dotenv import load_dotenv
from django.urls import reverse
import os
import paystack
from django.utils import timezone
from monnify_verification.monnify_api import *
from .models import Withdrawal, Transaction, Notification
from authentication.models import UserProfile
from .forms import UserUpdateForm, PaymentUpdate
from django.db.models import Sum
from datetime import datetime, timedelta
from .utils import check_expired_subscriptions
from krysline_admin.models import TransactionPIN
from django.contrib import messages as mg
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse


import uuid


load_dotenv()

# Create your views here.


@login_required(login_url='login')
@two_factor_required
# @kyc_required  # Optional: Only if you want to block dashboard until KYC is done
@rate_limit(rate='100000/hour')
@login_required
def dashboard(request):
    user = request.user
    profile = user.profile
    notification = Notification.objects.all().filter(user=user, is_read=False) 
    # notification = user.notifications.members.all()
    # print(notification.count())

    # 1. Fetch Affiliate Record Safely
    affiliate = getattr(user, 'affiliate_record', None)

    # 2. Security Check: Redirect if no affiliate, no package, or inactive

    # Setting Transaction PIN
    set_pin = False
    if TransactionPIN.objects.filter(user=request.user).exists():
        set_pin = True

    if not affiliate or not affiliate.is_active:
        return redirect('choose_package')

    if request.method == 'POST':
        pin = request.POST.get('pin')
        cpin = request.POST.get('cpin')

        trans_pin = TransactionPIN()

        if pin == cpin:
            trans_pin.user = request.user
            trans_pin.set_pin(pin)
            return redirect('dashboard')
        else:
            mg.error(request, 'PIN, Not matching, Try Again!')

    # 3. Financial Calculations (Withdrawals)
    # Total Paid Out (Approved)
    total_withdrawn = Withdrawal.objects.filter(
        user=user, status='approved'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # Total Currently Locked (Pending)
    pending_withdrawn = Withdrawal.objects.filter(
        user=user, status='pending'
    ).aggregate(total=Sum('amount'))['total'] or 0

    # 4. Commission Calculations
    commissions = CommissionLog.objects.filter(recipient_profile=profile)
    total_commission = commissions.aggregate(total=Sum('amount'))['total'] or 0

    latest_commissions = commissions.order_by('-created_at')[:10]

    # Current Balance from Profile
    current_balance = profile.balance

    # 5. Business Stats
    total_deposit = affiliate.package.price
    total_tx_count = PropertyTransaction.objects.filter(
        affiliate=affiliate,
        is_verified=True
    ).count()

    # 6. Rank Logic
    plan_name = affiliate.package.get_name_display()
    match str(affiliate.package.name).lower():
        case 'elite':
            rank_msg = "Elite Member (Max Depth + Spillover)"
        case 'professional' | 'premium':
            rank_msg = "Pro Member (3 Generations)"
        case _:
            rank_msg = "Basic Member (1 Generation)"

    context = {
        'affiliate': affiliate,
        'profile': profile,
        'current_balance': current_balance,
        'total_deposit': total_deposit,
        'total_withdrawn': total_withdrawn,
        'pending_withdrawn': pending_withdrawn,
        'total_tx_count': total_tx_count,
        'total_commission': total_commission,
        'plan_name': plan_name,
        'rank_msg': rank_msg,
        'latest_commissions': latest_commissions,
        'set_pin': set_pin,
        'is_active': affiliate.is_active,
        'notification': notification,
    }

    return render(request, 'users/user-dashboard.html', context)

@login_required(login_url="login")
def notify(request, pk):
    notification = get_object_or_404(Notification, id=pk)
    notification.mark_as_read()
    context = {
        "notification": notification
    }

    return render (request, 'notify.html', context)



@login_required(login_url='login')
@csrf_exempt
def mark_all_as_read(request):
    notify = Notification()
    notify.mark_all_as_read(user=request.user)
    return redirect("dashboard")



def courses(request):

    context = {

    }
    return render(request, 'users/course.html', context)


@login_required(login_url='login')
# Prevent script-kiddies from spamming packages
@rate_limit(rate='100000/hour')
@log_security_event(action='PACKAGE_SELECTION_START')
def choose_package(request):
    """
    View to display and securely process KAL Registration Packages.
    """
    user = request.user
    
    user_package = None
    is_active = False
    # 1. Security Check: If they already have a package, don't let them join again
    if hasattr(request.user, 'affiliate'):
        return redirect('dashboard')

    affiliate = getattr(user, 'affiliate_record', None)

    if affiliate:
        user_package = request.user.affiliate_record
        is_active = request.user.affiliate_record.is_active

    packages = AffiliatePackage.objects.all().order_by('price')

    # print(request.user.affiliate_record.is_active)
    context = {
        'packages': packages,
        'user_package': user_package,
        'is_active': is_active,
    }

    return render(request, 'users/plans.html', context)


@login_required(login_url="login")
def free_account_activation(request, pk):
    user = request.user
    package = get_object_or_404(AffiliatePackage, id=pk)
    affiliate = user.affiliate_record

    affiliate.package = package
    affiliate.duration = None
    affiliate.is_active = True 
    affiliate.save()

    return redirect('dashboard')




@login_required(login_url='login')
def package_payment(request, pk):
    user = request.user
    package = get_object_or_404(AffiliatePackage, id=pk)
    now = timezone.localtime(timezone.now())
    current_year = str(now.year)

    def generate_reference():
        return f"KAL-{package.id}-{user.id}-{uuid.uuid4().hex[:8]}-{current_year}"

    try:
        with transaction.atomic():
            # Lock row to prevent race condition
            user_invoice, _ = UserInvoice.objects.select_for_update().get_or_create(
                user=user,
                defaults={'inovoice_reference': ''}
            )

            reference = user_invoice.inovoice_reference or ''
            need_new_invoice = False

            # Check if existing reference is valid and matches current package
            if reference:
                try:
                    ref_parts = reference.split("-")
                    ref_package_id = int(ref_parts[1]) if len(ref_parts) > 1 else None
                except (IndexError, ValueError):
                    ref_package_id = None

                if ref_package_id == package.id:
                    invoice, valid = get_invoice(reference)

                    if valid:
                        status = invoice.get("invoiceStatus")

                        # Still pending → reuse checkout URL
                        if status == "PENDING":
                            response = HttpResponse()
                            response['HX-Redirect'] = invoice.get("checkoutUrl")
                            return response

                        # Already paid → check expiry
                        if status == "PAID":
                            expire_str = invoice.get('expiryDate')
                            if expire_str:
                                expire = datetime.strptime(expire_str, "%Y-%m-%d %H:%M:%S")
                                if timezone.is_aware(now):
                                    expire = timezone.make_aware(expire, now.tzinfo)
                                
                                if expire >= now:
                                    # Still active subscription
                                    messages.info(request, "You have an active subscription for this package.")
                                    return redirect("payments")
                            
                            # Expired paid subscription → create new
                            need_new_invoice = True
                            reference = generate_reference()

                        # Expired or cancelled → create new
                        elif status in ["EXPIRED", "CANCELLED"]:
                            need_new_invoice = True
                            reference = generate_reference()
                        
                        else:
                            # Unknown status → create new
                            need_new_invoice = True
                            reference = generate_reference()
                    else:
                        # Invalid invoice response → create new
                        need_new_invoice = True
                        reference = generate_reference()
                else:
                    # Different package → create new
                    need_new_invoice = True
                    reference = generate_reference()
            else:
                # No reference → create new
                need_new_invoice = True
                reference = generate_reference()

            # Create new invoice if needed
            if need_new_invoice:
                local_now = timezone.localtime(settings.DURATION)
                expiry_date = local_now.strftime("%Y-%m-%d %H:%M:%S")
                description = f"Subscription for {package.get_name_display()} Plan"

                invoice, valid = create_invoice(
                    amount=int(package.price),
                    user=user,
                    description=description,
                    reference=reference,
                    expiry_date=expiry_date
                )

                if not valid:
                    messages.error(request, "Unable to generate invoice. Please try again.")
                    print("Not generating")
                    return redirect("choose_package")

                # Save reference only after successful invoice creation
                user_invoice.inovoice_reference = reference
                user_invoice.save()

                response = HttpResponse()
                response['HX-Redirect'] = invoice.get("checkoutUrl")
                return response
            
            # Fallback - should not reach here
            return redirect("choose_package")

    except Exception as e:
        # Log the actual error for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Package payment error for user {user.id}, package {pk}: {str(e)}")
        
        messages.error(request, "Something went wrong. Please try again.")
        return redirect("choose_package")


# def package_payment(request, pk):
#     user = request.user
#     package = get_object_or_404(AffiliatePackage, id=pk)
#     now = timezone.localtime(timezone.now())
#     year = timezone.now()
#     year = str(datetime.now().date()).split("-")
#     # get_user_invoice_id = UserInvoice.objects.filter(user=user).first().inovoice_reference.split("-")[1]

#     def generate_reference():
#         return f"KAL-{package.id}-{user.id}-{uuid.uuid4().hex[:8]}-{year[0]}"

#     try:
#         with transaction.atomic():

#             # Lock row to prevent race condition
#             user_invoice = (
#                 UserInvoice.objects
#                 .select_for_update()
#                 .get_or_create(user=user)[0]
#             )

#             reference = user_invoice.inovoice_reference

#             # If reference exists → verify status
#             if reference and reference.split("-")[1] == package.id:

#                 invoice, valid = get_invoice(reference)

#                 if valid:

#                     status = invoice.get("invoiceStatus")

#                     # 🔹 Still payable → reuse
#                     if status == "PENDING":
#                         # return redirect(invoice.get("checkoutUrl"))
#                         response = HttpResponse()
#                         response['HX-Redirect'] = invoice.get("checkoutUrl")
#                         return response


#                     # 🔹 Already paid → stop duplicate payment
#                     if status == "PAID":
#                         expire = datetime.strptime(
#                             invoice['expiryDate'], "%Y-%m-%d %H:%M:%S")

#                         if timezone.is_aware(now):
#                             expire = timezone.make_aware(expire)

#                             if expire < now:
#                                 reference = generate_reference()
#                                 print("Paid alredy new reference", reference)
#                             else:
#                                 return redirect("payments")

#                     # 🔹 Expired / Cancelled → create new reference
#                     if status in ["EXPIRED", "CANCELLED"]:
#                         reference = generate_reference()

#                 else:
#                     reference = generate_reference()

#             else:
#                 reference = generate_reference()
                

#             local_now = timezone.localtime(settings.DURATION)
#             expiry_date = local_now.strftime("%Y-%m-%d %H:%M:%S")

#             description = f"Subscription for {package.get_name_display()} Plan"

#             # 🔹 Create invoice externally
#             invoice, valid = create_invoice(
#                 int(package.price),
#                 user,
#                 description,
#                 reference,
#                 expiry_date
#             )

#             if not valid:
#                 messages.error(request, "Unable to generate invoice.")
#                 return redirect("choose_package")

#             # 🔹 Save reference only after successful invoice creation
#             user_invoice.inovoice_reference = reference
#             user_invoice.save()

#             # return redirect(invoice.get("checkoutUrl"))
#             response = HttpResponse()
#             response['HX-Redirect'] = invoice.get("checkoutUrl")
#             return response

#     except Exception as e:
#         messages.error(request, "Something went wrong. Please try again.")
#         return redirect("choose_package")

# @login_required(login_url='login')
@csrf_exempt
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
                    #'referral_code': generate_referral_code()  # Ensure this exists
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
                    affiliate.duration and 
                    affiliate.duration > timezone.now()
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
                # affiliate.expires_at = timezone.now() + duration
                affiliate.save()

            # Distribute MLM commissions
            commissions_distributed = distribute_commissions(
                new_affiliate=affiliate, 
                new=True
            )
            
            if commissions_distributed:
                # Record successful transaction
                Transaction.objects.create(
                    user=user,
                    amount=package.price,
                    transaction_type='package_purchase',
                    description=f"Subscription: {package.get_name_display()} (Ref: {reference})",
                    #status='completed',
                    # reference=reference
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


# def payments(request):
#     reference = ""
#     payment_ref = request.GET.get('paymentReference')

#     if payment_ref:
#         reference = payment_ref
#     else:
#         reference = request.user.invoice.inovoice_reference

#     try:
#         invoice, valid = get_invoice(reference)

#         if valid and invoice['invoiceStatus'] == 'PAID':

#             package_id = invoice['invoiceReference'].split('-')[1]

#             description = invoice['description'].lower()

#             if "subscription" in description:

#                 with transaction.atomic():

#                     package = get_object_or_404(
#                         AffiliatePackage, id=package_id, price=float(invoice['amount']))
#                     print("Checking the Package:", package)

#                     user = get_object_or_404(
#                         User, email=invoice['customerEmail'])

#                     duration = settings.DURATION

#                     try:
#                         affiliate = Affiliate.objects.select_for_update().get(
#                             referral_code=str(user.affiliate_record.referral_code))

#                         if not affiliate.package:
#                             affiliate.package = package
#                             affiliate.save()

#                         if float(invoice['amount']) >= package.price:
#                             # SUCCESS: Activate user and trigger MLM Commissions
#                             affiliate.is_active = False
#                             affiliate.save()

#                             if not affiliate.is_active or affiliate.package.price < package.price:
#                                 affiliate.is_active = True
#                                 affiliate.duration = duration
#                                 affiliate.package = package
#                                 affiliate.save()

#                                 if distribute_commissions(new_affiliate=affiliate, new=True):
#                                     Transaction.objects.create(
#                                         user=user,
#                                         amount=package.price,
#                                         transaction_type='package_purchase',
#                                         description=f"Subscription Approved (Ref: {package.get_name_display()})"
#                                     )
#                                     return redirect('dashboard')
#                             else:
#                                 return redirect('dashboard')

#                     except Affiliate.DoesNotExist:
#                         affiliate2 = Affiliate.objects.create(
#                             user=user,
#                             package=package,
#                             duration=duration,
#                             is_active=True
#                         )
#                         affiliate2.save()

#                         if distribute_commissions(affiliate2):

#                             return redirect('dashboard')
#             else:
#                 print("Put withdrawal completion here")
#                 # TODO: verify payment for widthdrawal transfer
#         else:
#             messages.error(request, "Payment not successful")
#             return redirect('choose_package')

#     except Exception as e:
#         print(f"Verification Error: {e}")
#         messages.error(request, "Payment Not successful")
#         return redirect('choose_package')


@login_required(login_url='login')
@transaction.atomic
@rate_limit(rate='5/hour')  # Prevent script-kiddies from spamming packages
@log_security_event(action='TRANSACTION_CREATE')
def withdraw_funds(request):
    """
    Secure withdrawal logic for KAL Affiliates.
    Only allows withdrawal of earned commissions.
    """
    profile = request.user.profile

    user_pin = request.user.transaction_pin

    if not profile.account_number:
        messages.warning(
            request, "Please update your bank details to enable withdrawals.")
        # Build the URL: /user/profile/update/?next=/user/withdraw/
        dest_url = reverse('payment_update')
        return redirect(f"{dest_url}?next={request.path}")

    if request.method == 'POST':
        try:
            # 1. Get amount, Transaction_PIN and sanitize
            amount = Decimal(request.POST.get('amount', 0))
            if not user_pin.check_pin(request.POST.get('pin')):
                messages.error(request, "Invalid Transaction PIN.")
                return redirect('withdraw_funds')

            MIN_WITHDRAWAL = Decimal('2000.00')  # KAL Policy: Min ₦2k

            # 2. SECURITY CHECKS
            # A. Check if they have enough commission balance
            if amount > profile.balance:
                messages.error(request, "Insufficient commission balance.")
                return redirect('withdraw_funds')

            # B. Check for minimum withdrawal limit
            if amount < MIN_WITHDRAWAL:
                messages.error(
                    request, f"Minimum withdrawal is ₦{MIN_WITHDRAWAL}")
                return redirect('withdraw_funds')

            # 3. ATOMIC PROCESSING
            # We use select_for_update() to lock the profile row during the math
            user_profile = UserProfile.objects.select_for_update().get(id=profile.id)

            # Deduct from balance immediately (Hold the funds)
            user_profile.balance -= amount
            user_profile.save()

            # Create the withdrawal record
            Withdrawal.objects.create(
                user=request.user,
                amount=amount,
                status='pending'
            )

            messages.success(
                request, f"Withdrawal request for ₦{amount:,.2f} submitted successfully.")
            return redirect('dashboard')

        except ValueError:
            messages.error(request, "Invalid amount entered.")
    context = {
        'balance': profile.balance,
        'withdraw': True
    }

    return render(request, 'users/user-withdraw.html', context)


@login_required(login_url="login")
def withdraw_history(request):
    context = {
        "history": Withdrawal.objects.all().filter(user=request.user)
    }
    return render(request, 'users/withdraw-history.html', context)


@login_required(login_url='login')
def transaction_history(request):
    context = {
        "history": Transaction.objects.all().filter(user=request.user)
    }
    return render(request, 'users/transaction-history.html', context)


@login_required(login_url='login')
def referral_list(request):
    """
    Displays the list of users directly referred by the current user (Gen 1).
    """
    user_profile = request.user.profile
    user = request.user

    # 1. Fetch Affiliate Record Safely
    affiliate = getattr(user, 'affiliate_record', None)

    # Fetch all profiles where 'referrer' points to me
    # We use select_related to get the User and Affiliate data in one query (Performance)
    referrals = UserProfile.objects.filter(
        referrer=user_profile
    ).select_related('user', 'user__affiliate_record').order_by('-user__date_joined')

    # Calculate some stats for the top of the page
    total_referrals = referrals.count()
    active_referrals = referrals.filter(
        user__affiliate_record__is_active=True).count()
    pending_referrals = total_referrals - active_referrals

    commissions = CommissionLog.objects.filter(recipient_profile=user_profile)
    total_commission = commissions.aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'referrals': referrals,
        'total_referrals': total_referrals,
        'active_referrals': active_referrals,
        'pending_referrals': pending_referrals,
        'referral_url': f"{request.scheme}://{request.get_host()}/user/register/?ref={affiliate.referral_code}",
        'total_commission': total_commission
    }

    return render(request, 'users/user-referal.html', context)


@login_required(login_url="login")
@rate_limit(rate='5/hour')  # Prevent script-kiddies from spamming packages
@log_security_event(action='PROFILE_UPDATE')
def profile_update(request):

    error_msg = None
    profile = get_object_or_404(UserProfile, user=request.user)

    # print(profile.user.email)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user.profile)

        if form.is_valid():
            address = form.cleaned_data.get('address')
            state = form.cleaned_data.get('state')
            zip_code = form.cleaned_data.get('zip_code')
            city = form.cleaned_data.get('city')
            country = form.cleaned_data.get('country')

            # Initialize User for updating
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')

            # Updating the user profile
            profile.address = address
            profile.state = state
            profile.zip_code = zip_code
            profile.city = city
            profile.country = country

            profile.save()

            profile.user.first_name = first_name
            profile.user.last_name = last_name
            profile.user.save()

            messages.success(request, 'Profile Updated Successfully!')
            return redirect('profile_update')
        else:
            errors = form.errors.get_json_data(escape_html=True)
            for error in errors:
                error_msg = errors[error][0]['message']

            messages.error(request, error_msg)

    context = {
        'update': True
    }

    return render(request, 'users/user-profile-setting.html', context)


@log_security_event(action="PROFILE_UPDATE")
@login_required(login_url="login")
@rate_limit('5/hour')
def payment_update(request):
    profile = request.user.profile

    url = request.META.get("HTTP_REFERER")

    if request.method == 'POST':
        form = PaymentUpdate(request.POST, instance=profile)
        if form.is_valid():
            bank = form.cleaned_data.get('bank')
            account_name = form.cleaned_data.get('account_name')
            account_number = form.cleaned_data.get('account_number')

            # Updating the Profile Bank Details
            profile.account_name = account_name
            profile.account_number = account_number
            profile.bank = bank
            profile.save()

            messages.success(request, 'Payment System Updated Successfully!')

            try:
                query = requests.utils.urlparse(url).query
                params = dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage = params['next']
                    return redirect(nextPage)
            except:
                return redirect("payment_update")

    context = {
        'payment': True
    }
    return render(request, 'users/user-payment.html', context)


def user_pin_change(request):
    obj_pin = TransactionPIN()

    if request.method == 'POST':
        pin = request.POST.get('pin')
        cpin = request.POST.get('cpin')
        current_pin = request.POST.get('current_pin')

        if pin == cpin:
            try:
                user_pin = TransactionPIN.objects.get(user=request.user)

                if user_pin.check_pin(current_pin):
                    user_pin.set_pin(pin)
                    mg.success(request, 'PIN Updated successfully!')
                    return redirect('change_pin')
                else:
                    mg.error(
                        request, 'PIN verification failed! Try Again, Account will be Locked after 4 attempts')
                    
            except TransactionPIN.DoesNotExist:
                obj_pin.user = request.user
                obj_pin.set_pin(pin)
                mg.success(request, 'PIN Updated successfully!')
                return redirect('change_pin')
        else:
            mg.error(request, 'New PIN & Confirmation PIN does not match!')

    return render(request, 'users/pin.html')


def verify_bank_account(request):

    # Getting the Account and bank name from the user
    accountNumber = request.POST.get("account_number")
    bankName = request.POST.get("bank")

    details, valid = bank_verification(accountNumber, bankName)

    context = {
        'accountName': details["accountName"],
        'fetched': valid
    }

    return render(request, 'users/account.html', context)
