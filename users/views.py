from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from security.decorators import *
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
from affiliation.models import AffiliatePackage, CommissionLog, PropertyTransaction, Affiliate
from affiliation.services import *
from dotenv import load_dotenv
import os
import paystack
from .models import Withdrawal, Transaction
from authentication.models import UserProfile
from django.db.models import Sum

load_dotenv()

# Create your views here.
@login_required(login_url='login')
@two_factor_required
#@kyc_required  # Optional: Only if you want to block dashboard until KYC is done
@rate_limit(rate='60/minute')
@login_required
def dashboard(request):
    user = request.user
    profile = user.profile
    
    # 1. Fetch Affiliate Record Safely
    affiliate = getattr(user, 'affiliate_record', None)

    # 2. Security Check: Redirect if no affiliate, no package, or inactive
    if not affiliate or not affiliate.is_active or not affiliate.package:
        return redirect('choose_package')

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
        'referral_url': f"{request.scheme}://{request.get_host()}/user/register/?ref={affiliate.referral_code}",
    }

    return render(request, 'users/user-dashboard.html', context)








@login_required(login_url='login')
@rate_limit(rate='100/hour') # Prevent script-kiddies from spamming packages
@log_security_event(action='PACKAGE_SELECTION_START')
def choose_package(request):
    """
    View to display and securely process KAL Registration Packages.
    """
    # 1. Security Check: If they already have a package, don't let them join again
    if hasattr(request.user, 'affiliate'):
        return redirect('dashboard')

    packages = AffiliatePackage.objects.filter(is_active=True).order_by('price')



    if request.method == "POST":
        package_id = request.POST.get('package_id')
        referrer_code = request.POST.get('referrer_code', '').strip()

        # 2. Secure Fetch: Get package by ID from DB, NOT the price from POST
        selected_package = get_object_or_404(AffiliatePackage, id=package_id, is_active=True)

        # 3. Referrer Validation: Handle the upline logic
        upline = None
        if referrer_code:
            upline = Affiliate.objects.filter(referral_code=referrer_code).first()

        # 4. Atomic Transaction: Create Affiliate profile safely
        try: 
            with transaction.atomic():
                new_affiliate = Affiliate.objects.create(
                    user=request.user,
                    upline=upline,
                    package=selected_package,
                    is_active=False # Keep inactive until payment is confirmed
                )
                
                # Store the package_id in session for the Payment Gateway (Paystack/Flutterwave)
                request.session['pending_registration_id'] = new_affiliate.id
                
                # Redirect to your Payment Page
                return redirect('process_payment')

        except Exception as e:
            logger.error("package_selection_failed", user=request.user.email, error=str(e))
            return render(request, 'onboarding/choose_package.html', {
                'packages': packages,
                'error': "An error occurred. Please try again."
            })
        
    # print()
    context = {
        'packages': packages,
        'user_package': request.user.affiliate_record
    }

    return render(request, 'users/plans.html', context)


@login_required(login_url='login')
def payments(request):
    user = request.user
    
    try:
        paystack.api_key = os.environ.get('SECRET_KEY')

        # status = request.GET.get('status')
        tx_ref = request.GET.get('reference')


        response = paystack.Transaction.verify(tx_ref)

        if response.status and response.data["status"] == "success":

            amount = response.data["amount"]/100
            with transaction.atomic():
                package = get_object_or_404(AffiliatePackage, price=float(amount))
                try:
                    affiliate = Affiliate.objects.select_for_update().get(referral_code=str(user.affiliate_record.referral_code))
                    
                    if float(amount) >= package.price:
                        # SUCCESS: Activate user and trigger MLM Commissions
                        affiliate.is_active = True
                        affiliate.save()
                        
                        print("Normal", affiliate)
                        # Trigger your MLM commission distribution logic
                        # distribute_commissions(affiliate.user.profile)

                        if distribute_commissions(affiliate):
                            return redirect('dashboard')
                    

                except Affiliate.DoesNotExist:
                    Affiliate.objects.create(
                        user = user,
                        package = package
                    )

        else:
            messages.error(request, "Payment not successful")
            return redirect('choose_package')
    

    except Exception as e:
        print(f"Verification Error: {e}")
    
    




@login_required(login_url='login')
@transaction.atomic
def withdraw_funds(request):
    """
    Secure withdrawal logic for KAL Affiliates.
    Only allows withdrawal of earned commissions.
    """
    profile = request.user.profile

    package_price = int(request.user.affiliate_record.package.price)
    
    if request.method == 'POST':
        try:
            # 1. Get amount and sanitize
            amount = Decimal(request.POST.get('amount', 0))
            MIN_WITHDRAWAL = Decimal('100.00') # KAL Policy: Min ₦2k

            # 2. SECURITY CHECKS
            # A. Check if they have enough commission balance
            if amount > (profile.balance - package_price):
                messages.error(request, "Insufficient commission balance.")
                return redirect('withdraw_funds')

            # B. Check for minimum withdrawal limit
            if amount < MIN_WITHDRAWAL:
                messages.error(request, f"Minimum withdrawal is ₦{MIN_WITHDRAWAL}")
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

            messages.success(request, f"Withdrawal request for ₦{amount:,.2f} submitted successfully.")
            return redirect('dashboard')

        except ValueError:
            messages.error(request, "Invalid amount entered.")

    return render(request, 'users/user-withdraw.html', {'balance': profile.balance})




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
    
    # Fetch all profiles where 'referrer' points to me
    # We use select_related to get the User and Affiliate data in one query (Performance)
    referrals = UserProfile.objects.filter(
        referrer=user_profile
    ).select_related('user', 'user__affiliate_record').order_by('-user__date_joined')

    # Calculate some stats for the top of the page
    total_referrals = referrals.count()
    active_referrals = referrals.filter(user__affiliate_record__is_active=True).count()
    pending_referrals = total_referrals - active_referrals

    context = {
        'referrals': referrals,
        'total_referrals': total_referrals,
        'active_referrals': active_referrals,
        'pending_referrals': pending_referrals,
    }

    return render(request, 'users/user-referal.html', context)