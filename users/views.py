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
from .models import Withdrawal, Transaction
from authentication.models import UserProfile
from .forms import UserUpdateForm, PaymentUpdate
from django.db.models import Sum
from datetime import datetime, timedelta
from .utils import check_expired_subscriptions
from krysline_admin.models import TransactionPIN
from django.contrib import messages as mg
from django.conf import settings


load_dotenv()

# Create your views here.


@login_required(login_url='login')
@two_factor_required
# @kyc_required  # Optional: Only if you want to block dashboard until KYC is done
@rate_limit(rate='6/minute')
@login_required
def dashboard(request):
    user = request.user
    profile = user.profile

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
        'is_active': affiliate.is_active
    }

    return render(request, 'users/user-dashboard.html', context)


@login_required(login_url='login')
@rate_limit(rate='1000/hour')  # Prevent script-kiddies from spamming packages
@log_security_event(action='PACKAGE_SELECTION_START')
def choose_package(request):
    """
    View to display and securely process KAL Registration Packages.
    """
    # 1. Security Check: If they already have a package, don't let them join again
    if hasattr(request.user, 'affiliate'):
        return redirect('dashboard')

    packages = AffiliatePackage.objects.all().order_by('price')

    

    # print(request.user.affiliate_record.is_active)
    context = {
        'packages': packages,
        'user_package': request.user.affiliate_record,
        'is_active': request.user.affiliate_record.is_active,
    }

    return render(request, 'users/plans.html', context)


def package_payment(request, pk):
    import uuid

    user = request.user
    package = get_object_or_404(AffiliatePackage, id=pk)
    now = timezone.localtime(timezone.now())
    year = timezone.now()
    year = str(datetime.now().date()).split("-")

    reference = ''

    try:
        userInvoiceReference = UserInvoice.objects.filter(user=user)
        if userInvoiceReference:
            reference = userInvoiceReference.first().inovoice_reference

            invoice, valid = get_invoice(reference)
            if valid:
                if invoice['invoiceStatus'] == "PENDING":
                    url = invoice['checkoutUrl']
                    return redirect(url)

                if invoice['invoiceStatus'] == "PAID":
                    expire = datetime.strptime(
                        invoice['expiryDate'], "%Y-%m-%d %H:%M:%S")

                    if timezone.is_aware(now):
                        expire = timezone.make_aware(expire)

                    # Checking if invoice has expired
                    if expire < now or invoice['invoiceStatus'] == 'EXPIRED' or invoice['invoiceStatus'] == 'CANCELLED':
                        reference = f"KAL-{package.name}-{user.username}-{uuid.uuid4()}-{year[0]}"
                        print(reference)
                    else:
                        return redirect('payments')
                else: 
                    reference = f"KAL-{package.name}-{user.username}-{uuid.uuid4()}-{year[0]}"
                    

        description = f"Subscription for the {package.name.capitalize()} Plan - {package.get_name_display()}"
        local_now = timezone.localtime(settings.DURATION)

        
        # 2. Format it
        expiry_date = local_now.strftime("%Y-%m-%d %H:%M:%S")

        # update user invoice reference
        userInvoice = UserInvoice.objects.filter(user=user).first()
        userInvoice.inovoice_reference = reference
        userInvoice.save()

        # Generating new Invoice 
        invoice, valid = create_invoice(
            int(package.price),
            user,
            description,
            userInvoice.inovoice_reference,
            expiry_date
        )


        if valid:
            print(invoice, 'Original Created')
            url = invoice['checkoutUrl']
            return redirect(url)
        else:
            messages.error(request, "Unable to generate invoice")
            return redirect('choose_package')
    except:
        messages.error(request, 'Please Try Again!')
        return redirect('choose_package') 


@login_required(login_url='login')
def payments(request):
    reference = ""
    payment_ref = request.GET.get('paymentReference')

    if payment_ref:
        reference = payment_ref
    else:
        reference = request.user.invoice.inovoice_reference


    try:
        invoice, valid = get_invoice(reference)

  
        if valid and invoice['invoiceStatus'] == 'PAID':

            package_name = invoice['invoiceReference'].split('-')[1]

            description = invoice['description'].lower()

            if "subscription" in description:

                with transaction.atomic():

                    package = get_object_or_404(
                        AffiliatePackage, name=package_name, price=float(invoice['amount']))

                    user = get_object_or_404(
                        User, email=invoice['customerEmail'])

                    duration = settings.DURATION

                    try:
                        affiliate = Affiliate.objects.select_for_update().get(
                            referral_code=str(user.affiliate_record.referral_code))

                        if not affiliate.package:
                            affiliate.package = package
                            affiliate.save()

                        if float(invoice['amount']) >= package.price:
                            # SUCCESS: Activate user and trigger MLM Commissions
                            
                            affiliate.is_active = True
                            affiliate.duration = duration
                            affiliate.package = package
                            affiliate.save()

                            if distribute_commissions(new_affiliate=affiliate, new=True):
                                Transaction.objects.create(
                                    user=user,
                                    amount=package.price,
                                    transaction_type='package_purchase',
                                    description=f"Subscription Approved (Ref: {package.get_name_display()})"
                                )
                                return redirect('dashboard')
                                

                    except Affiliate.DoesNotExist:
                        affiliate2 = Affiliate.objects.create(
                            user=user,
                            package=package,
                            duration=duration,
                            is_active=True
                        )
                        affiliate2.save()

                        if distribute_commissions(affiliate2):

                            return redirect('dashboard')
            else:
                print("Put withdrawal completion here")
                # TODO: verify payment for widthdrawal transfer
        else:
            messages.error(request, "Payment not successful")
            return redirect('choose_package')

    except Exception as e:
        print(f"Verification Error: {e}")
        messages.error(request, "Payment Not successful")
        return redirect('choose_package')


@login_required(login_url='login')
@transaction.atomic
@rate_limit(rate='5/minute')  # Prevent script-kiddies from spamming packages
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
@rate_limit(rate='100/hour')  # Prevent script-kiddies from spamming packages
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
@rate_limit('10/minute')
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
