from django.shortcuts import render, redirect, get_list_or_404, get_object_or_404
from security.decorators import *
from django.contrib.auth.decorators import login_required
from affiliation.models import AffiliatePackage, CommissionLog, PropertyTransaction, Affiliate

# Create your views here.
@login_required
@two_factor_required
#@kyc_required  # Optional: Only if you want to block dashboard until KYC is done
@rate_limit(rate='60/minute')
def user_dashboard(request):
    """
    Main Affiliate Dashboard showing earnings and downline stats.
    """
    user = request.user
    
    # Use 'getattr' to safely fetch the affiliate profile
    affiliate = getattr(user, 'affiliate', None)
    profile = getattr(user, 'profile', None)

    if not affiliate or not profile:
        # If they haven't picked a package yet, send them to onboarding
        return redirect('choose_package')

    # Fetch stats for the dashboard
    recent_transactions = PropertyTransaction.objects.filter(
        affiliate=affiliate, 
        is_verified=True
    )[:5]
    
    # Get total earnings from your CommissionLog model
    commissions = CommissionLog.objects.filter(recipient=profile)
    total_earned = sum(c.amount for c in commissions)

    # Use 'match' to set a status message based on their package
    match affiliate.package.name:
        case 'elite':
            rank_msg = "You are an Elite Member (Max Earnings + Spillover)"
        case 'professional' | 'premium':
            rank_msg = "You are a Pro Member (3 Generations active)"
        case _:
            rank_msg = "Basic Affiliate (1 Generation active)"

    context = {
        'affiliate': affiliate,
        'profile': profile,
        'recent_transactions': recent_transactions,
        'total_earned': total_earned,
        'rank_msg': rank_msg,
        'referral_url': f"{request.scheme}://{request.get_host()}/register/?ref={affiliate.referral_code}",
        'downline_count': affiliate.downlines.count(),
    }

    return render(request, 'dashboard/index.html', context)
# TODO Change the template to original 





@login_required
@rate_limit(rate='10/hour') # Prevent script-kiddies from spamming packages
@log_security_event(action='PACKAGE_SELECTION_START')
def choose_package(request):
    """
    View to display and securely process KAL Registration Packages.
    """
    # 1. Security Check: If they already have a package, don't let them join again
    if hasattr(request.user, 'affiliate'):
        return redirect('secure_dashboard')

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

    return render(request, 'onboarding/choose_package.html', {'packages': packages})
    # TODO Change the template to original 