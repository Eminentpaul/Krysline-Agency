from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Sum, Count, Q
from decimal import Decimal
from krysline_admin.models import TransactionPIN
from users.models import Withdrawal
from security.decorators import rate_limit, get_client_ip, log_security_event, logger
from .models import InvestmentPlan, Investment, InvestmentStatus, InvestmentPayout
from affiliation.models import AffiliatePackage
from authentication.forms import AffiliateRegistrationForm
from security.security_utils import *
from authentication.token import email_verification_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
import requests
from django.core.mail import EmailMessage
# Email Require
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from authentication.models import User

# Create your views here.


def package(request):
    packages = AffiliatePackage.objects.all().order_by('price')

    context = {
        "packages": packages
    }

    return render(request, 'base/plans.html', context)


@log_security_event(action='USER_INVESTOR_REGISTRATION_ATTEMPT')
def register(request): 
    invest = True
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    initial_data =  request.GET.get('ref', '')
    error_msg = None
    form = ''

    if request.method == 'POST':
        # referrer_code = request.POST.get("referrer_code")

        form = AffiliateRegistrationForm(request.POST)
        
        if form.is_valid():

            referrer_code = request.POST.get("referrer_code") # Capture from form

            if referrer_code:
                request.session['pending_referrer'] = referrer_code
            try:
                with transaction.atomic():
                    # Save user (password is hashed automatically by the form)
                    

                    user = form.save()

                    
                    # Generate Verification Link
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = email_verification_token.make_token(user)
                    link = f"{request.scheme}://{request.get_host()}/user/activate/{uid}/{token}/"

                    # Send Email
                    subject = "Verify your KAL Affiliate Account"
                    message = render_to_string('authentication/acc_active_email.html', {
                        'user': user,
                        'domain': request.get_host(),
                        'link': link,
                    })

                    text_content = strip_tags(message)

                    email = EmailMultiAlternatives(subject, text_content, to=[user.email])
                    # email = EmailMessage(subject, message, to=[user.email])
                    email.attach_alternative(message, 'text/html')
                    email.send()
                    
                    # Log success
                    logger.info("registration_successful", user=user.email)
                    
                    # Log the user in immediately
                    # login(request, user)
                    
                    # # Redirect to package selection to start the affiliate process
                    # return redirect('choose_package')
                    return render(request, 'authentication/verify_email_sent.html')
                
            except Exception as e:
                logger.error("registration_error", error=str(e))
                form.add_error(None, "An internal error occurred. Please try again.")
        else:
            errors = form.errors.get_json_data(escape_html=True)
            for error in errors:
                error_msg = errors[error][0]['message']

            messages.error(request, error_msg)

    return render(request, 'authentication/register.html', {'initial_data': initial_data, 'invest': invest})



def investment_plans_list(request):
    """Display all active investment plans with calculator"""
    plans = InvestmentPlan.objects.filter(
        is_active=True).order_by('min_amount')
    active_investment = Investment.objects.filter(user=request.user,
        status=InvestmentStatus.ACTIVE).first()
    
   
    context = {
        'plans': plans,
        'title': 'Investment Plans',
        'active_investment': active_investment,
    }
    return render(request, 'base/plan_list.html', context)


@login_required()
def investment_detail(request, slug):
    """Detail view for specific investment plan"""
    plan = get_object_or_404(InvestmentPlan, slug=slug, is_active=True)

    # Calculate example returns
    example_amount = plan.min_amount
    total_return = plan.calculate_total_return(example_amount)
    payout_amount = plan.calculate_payout_amount(example_amount)

    # Check if user has active investment in this plan
    user_investment = None
    if request.user.is_authenticated:
        user_investment = Investment.objects.filter(
            user=request.user,
            plan=plan,
            status__in=[InvestmentStatus.ACTIVE, InvestmentStatus.PENDING]
        ).first()

    context = {
        'plan': plan,
        'example_amount': example_amount,
        'total_return': total_return,
        'payout_amount': payout_amount,
        'user_investment': user_investment,
    }
    return render(request, 'investments/plan_detail.html', context)


@login_required
def create_investment(request, plan_slug):
    """Create new investment view"""
    plan = get_object_or_404(InvestmentPlan, slug=plan_slug, is_active=True)

    # Pre-calculate example values for template
    plan.example_return = plan.calculate_total_return(plan.min_amount)
    plan.example_payout_amount = plan.calculate_payout_amount(plan.min_amount)

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))

        # Validation
        if amount < plan.min_amount:
            messages.error(
                request, f"Minimum investment is ₦{plan.min_amount:,.2f}")
            return redirect('create_investment', plan_slug=plan_slug)

        if plan.max_amount and amount > plan.max_amount:
            messages.error(
                request, f"Maximum investment is ₦{plan.max_amount:,.2f}")
            return redirect('create_investment', plan_slug=plan_slug)

        # Check for existing active investment in this plan
        existing = Investment.objects.filter(
            user=request.user,
            plan=plan,
            status__in=[InvestmentStatus.PENDING, InvestmentStatus.ACTIVE]
        ).exists()

        if existing:
            messages.warning(
                request, "You already have an active or pending investment in this plan.")
            return redirect('my_investments')

        # Create investment
        try:
            with transaction.atomic():
                investment = Investment.objects.create(
                    user=request.user,
                    plan=plan,
                    amount=amount,
                    status=InvestmentStatus.PENDING
                )

                # Create payout schedule
                _create_payout_schedule(investment)

            messages.success(
                request,
                f"Investment request created! Reference: {investment.reference_code}. "
                "Please proceed to payment to complete your investment."
            )
            return redirect('upload_payment_proof', investment_id=investment.id)

        except Exception as e:
            messages.error(request, "An error occurred. Please try again.")
            return redirect('create_investment', plan_slug=plan_slug)

    context = {
        'plan': plan,
    }
    return render(request, 'base/create_investment.html', context)


def _create_payout_schedule(investment):
    """Create scheduled payouts for an investment"""
    plan = investment.plan
    payout_amount = plan.calculate_payout_amount(investment.amount)
    principal_per_payout = investment.amount / plan.total_payouts
    return_per_payout = (plan.calculate_total_return(
        investment.amount) / plan.total_payouts)

    for i in range(1, plan.total_payouts + 1):
        months_from_start = (i) * plan.payout_frequency_months
        scheduled_date = timezone.now() + timezone.timedelta(days=months_from_start * 31)

        InvestmentPayout.objects.create(
            investment=investment,
            payout_number=i,
            principal_amount=principal_per_payout,
            return_amount=return_per_payout,
            scheduled_date=scheduled_date
        )


@login_required
def upload_payment_proof(request, investment_id):
    """Handle payment proof upload"""
    investment = get_object_or_404(
        Investment,
        id=investment_id,
        user=request.user,
        status=InvestmentStatus.PENDING
    )

    if request.method == 'POST':
        # Validate required fields
        bank_used = request.POST.get('bank_used')
        amount_paid = request.POST.get('amount_paid')
        # payment_date = request.POST.get('payment_date')
        transaction_reference = request.POST.get('transaction_reference')
        payment_proof = request.FILES.get('payment_proof')
        notes = request.POST.get('notes', '')

        # Validation
        if not all([bank_used, amount_paid, payment_proof]):
            messages.error(
                request, "Please fill in all required fields and upload payment proof.")
            return redirect('upload_payment_proof', investment_id=investment_id)

        # Validate amount matches
        if Decimal(amount_paid) != investment.amount:
            messages.error(
                request, "Amount paid must match investment amount.")
            return redirect('upload_payment_proof', investment_id=investment_id)

        # Save payment details
        investment.payment_proof = payment_proof
        investment.admin_notes = (
            f"Bank: {bank_used}\n"
            f"Transaction Ref: {transaction_reference}\n"
            f"Payment Date: {investment.investment_date}\n"
            f"Notes: {notes}"
        )
        investment.save()

        messages.success(
            request,
            "Payment proof uploaded successfully! Your investment is pending verification. "
            "You will be notified once approved."
        )
        return redirect('dashboard')

    context = {
        'investment': investment,
    }
    return render(request, 'base/upload_payment_proof.html', context)


@login_required
def my_investments(request):
    """Display all user investments with summary statistics"""
    user = request.user

    # Get all investments with related data
    investments = Investment.objects.filter(
        user=user
    ).select_related(
        'plan'
    ).prefetch_related(
        'payouts'
    ).order_by('-created_at')

    # Calculate summary statistics
    stats = investments.aggregate(
        total_invested=Sum('amount', filter=Q(
            status__in=['active', 'completed'])),
        total_returns=Sum('total_paid_out'),
        active_count=Count('id', filter=Q(status='active')),
        pending_count=Count('id', filter=Q(status='pending')),
        completed_count=Count('id', filter=Q(status='completed')),
    )

    # Calculate pending returns (scheduled but not yet paid)
    pending_returns = InvestmentPayout.objects.filter(
        investment__user=user,
        status='scheduled',
        investment__status='active'
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    # Total payouts received
    total_payouts_received = InvestmentPayout.objects.filter(
        investment__user=user,
        status='completed'
    ).count()

    # Enhance investments with recent payouts for display
    for inv in investments:
        inv.recent_payouts = inv.payouts.all()[:3]  # Last 3 payouts

    context = {
        'investments': investments,
        'total_invested': stats['total_invested'] or 0,
        'total_returns_earned': stats['total_returns'] or 0,
        'pending_returns': pending_returns,
        'total_payouts_received': total_payouts_received,
        'active_count': stats['active_count'],
        'pending_count': stats['pending_count'],
        'completed_count': stats['completed_count'],
    }

    return render(request, 'base/my_investments.html', context)


@login_required
def investment_dashboard(request):
    """Dashboard view for investors"""
    user = request.user

    if user.user_type != 'investor':
        return redirect("login") 
    
    

    set_pin = False
    if TransactionPIN.objects.filter(user=request.user).exists():
        set_pin = True

    # Get user's investments
    investments = Investment.objects.filter(user=user).select_related('plan')
    active_investment = investments.filter(
        status=InvestmentStatus.ACTIVE).first()
    
    # Pending Withdrawal
    withdrawls = Withdrawal.objects.all().filter(user=user)
    pending_withdrawal = sum(withd.amount for withd in withdrawls if withd.status=="pending")
    total_withdrawal = sum(withd.amount for withd in withdrawls if withd.status=="approved")

    # Calculate totals
    total_invested = sum(
        inv.amount for inv in investments
        if inv.status in [InvestmentStatus.ACTIVE, InvestmentStatus.COMPLETED]
    )
    total_returns_earned = sum(inv.total_paid_out for inv in investments)

    # Pending/scheduled returns
    pending_returns = 0
    next_payout_date = None
    if active_investment:
        next_payout = active_investment.next_payout_date
        if next_payout:
            next_payout_date = next_payout
            # Get next pending payout amount
            next_payout_obj = active_investment.payouts.filter(
                status=InvestmentPayout.PayoutStatus.SCHEDULED,
                payout_number=active_investment.payouts_completed + 1
            ).first()
            if next_payout_obj:
                pending_returns = next_payout_obj.total_amount

    # Stats
    active_investments_count = investments.filter(
        status=InvestmentStatus.ACTIVE).count()
    total_payouts_received = sum(inv.payouts_completed for inv in investments)

    if not active_investments_count:
        return redirect('investment_plans')

    # Recent payouts
    recent_payouts = InvestmentPayout.objects.filter(
        investment__user=user,
        status=InvestmentPayout.PayoutStatus.COMPLETED
    ).select_related('investment', 'investment__plan').order_by('-processed_date')[:10]

    # Available plans for quick view
    available_plans = InvestmentPlan.objects.filter(is_active=True)[:3]

    # Chart data (last 6 months)
    from datetime import timedelta
    from django.db.models import Sum

    chart_labels = []
    chart_data = []
    chart_returns = []

    for i in range(5, -1, -1):
        month_date = timezone.now() - timedelta(days=30*i)
        chart_labels.append(month_date.strftime('%b'))

        # Cumulative investment up to that month
        month_investments = investments.filter(
            investment_date__lte=month_date,
            status__in=[InvestmentStatus.ACTIVE, InvestmentStatus.COMPLETED]
        ).aggregate(total=Sum('amount'))['total'] or 0
        chart_data.append(float(month_investments))

        # Returns earned up to that month
        month_returns = sum(
            p.total_amount for p in InvestmentPayout.objects.filter(
                investment__user=user,
                status=InvestmentPayout.PayoutStatus.COMPLETED,
                processed_date__lte=month_date
            )
        )
        chart_returns.append(float(month_returns))

    # Available withdrawal (completed payouts not yet withdrawn)
    # Adjust based on your withdrawal logic
    available_withdrawal = user.profile.balance


    context = {
        'total_invested': total_invested,
        'total_returns_earned': total_returns_earned,
        'pending_returns': pending_returns,
        'next_payout_date': next_payout_date,
        'active_investments_count': active_investments_count,
        'total_payouts_received': total_payouts_received,
        'active_investment': active_investment,
        'recent_payouts': recent_payouts,
        'available_plans': available_plans,
        'available_withdrawal': available_withdrawal,
        'set_pin': set_pin,
        'pending_withdrawal': pending_withdrawal,
        'total_withdrawal': total_withdrawal,

        # Chart data
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'chart_returns': chart_returns,
    }

    return render(request, 'base/investor.html', context)


# Admin/Staff Views


@staff_member_required
def admin_investment_list(request):
    """Admin view to list all investments"""
    status_filter = request.GET.get('status')

    investments = Investment.objects.all().select_related('user', 'plan')

    if status_filter:
        investments = investments.filter(status=status_filter)

    context = {
        'investments': investments,
        'status_choices': InvestmentStatus.choices,
        'current_filter': status_filter,
    }
    return render(request, 'investments/admin_list.html', context)


@staff_member_required
def verify_investment(request, investment_id):
    """Admin verification of investment payment"""
    investment = get_object_or_404(
        Investment, 
        id=investment_id, 
        status=InvestmentStatus.PENDING
    )

    if request.method == 'POST':
        # Check which form was submitted based on URL or hidden field
        # The template has separate forms for approve and reject
        
        # Check if this is a rejection (reject form submits to reject_investment URL)
        # or approval (approve form submits to verify_investment URL)
        
        # Since template posts approve to verify_investment and reject to reject_investment,
        # we only handle approval here. Rejection is handled by reject_investment view.
        
        notes = request.POST.get('verification_notes', '')

        with transaction.atomic():
            investment.status = InvestmentStatus.ACTIVE
            investment.payment_verified_by = request.user
            investment.payment_verified_at = timezone.now()
            investment.admin_notes = notes
            investment.save()  # This triggers start_date and maturity_date calculation

            # Update first payout to scheduled
            first_payout = investment.payouts.first()
            if first_payout:
                first_payout.status = InvestmentPayout.PayoutStatus.SCHEDULED
                first_payout.save()

        messages.success(
            request, 
            f"Investment {investment.reference_code} approved and activated."
        )
        return redirect('admin_investment_management')

    context = {
        'investment': investment,
        # Add any additional context needed by template
        'status_choices': InvestmentStatus.choices if hasattr(InvestmentStatus, 'choices') else [],
    }
    return render(request, 'base/verify_investment.html', context)




def _404(request, exception):
    return render(request, '404.html', {})
