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

load_dotenv()

# Create your views here.
@login_required(login_url='login')
@two_factor_required
#@kyc_required  # Optional: Only if you want to block dashboard until KYC is done
@rate_limit(rate='60/minute')
def dashboard(request):
    """
    Main Affiliate Dashboard showing earnings and downline stats.
    """
    user = request.user
    
    

    if not user.affiliate_record.is_active:
        # If they haven't picked a package yet, send them to onboarding
        return redirect('choose_package')

    # Fetch stats for the dashboard
    recent_transactions = PropertyTransaction.objects.filter(
        affiliate=user.affiliate_record, 
        is_verified=True
    )[:5]
    
    # Get total earnings from your CommissionLog model
    commissions = CommissionLog.objects.filter(recipient_profile=user.profile)
    total_earned = sum(c.amount for c in commissions)

    # Use 'match' to set a status message based on their package
    match str(user.affiliate_record.package.name).lower():
        case 'elite':
            rank_msg = "You are an Elite Member (Max Earnings + Spillover)"
        case 'professional' | 'premium':
            rank_msg = "You are a Pro Member (3 Generations active)"
        case _:
            rank_msg = "Basic Affiliate (1 Generation active)"

    context = {
        'affiliate': user.affiliate_record,
        'profile': user.profile,
        'recent_transactions': recent_transactions,
        'total_earned': total_earned,
        'rank_msg': rank_msg,
        'referral_url': f"{request.scheme}://{request.get_host()}/user/register/?ref={user.affiliate_record.referral_code}",
        # 'downline_count': user.affiliate_record.downlines.count(),
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
    context = {
        'packages': packages
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
                        
                        # Trigger your MLM commission distribution logic
                        # distribute_commissions(affiliate.user.profile)

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
    
    







# # @login_required
# # def payment_callback(request):
# #     """
# #     Handles the GET redirect from Flutterwave after payment.
# #     URL: /Dashboard/payments/?status=completed&tx_ref=...
# #     """
# #     status = request.GET.get('status')
# #     tx_ref = request.GET.get('tx_ref')
# #     transaction_id = request.GET.get('transaction_id')

#     if status == 'completed' or status == 'successful':
#         # 🛡️ SECURITY: Always re-verify with the API, never trust the URL params
#         if verify_transaction_with_api(transaction_id):
#             messages.success(request, "Payment successful! Your KAL account is now active.")
#             return redirect('secure_dashboard')
#         else:
#             messages.error(request, "Verification failed. Please contact KAL support.")
# #     else:
# #         messages.error(request, "Payment was cancelled or failed.")
    
# #     return redirect('choose_package')