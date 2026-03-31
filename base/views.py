from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.http import JsonResponse
from decimal import Decimal
from krysline_admin.models import TransactionPIN

from .models import InvestmentPlan, Investment, InvestmentStatus, InvestmentPayout
from affiliation.models import AffiliatePackage

# Create your views here.


def package(request):
    packages = AffiliatePackage.objects.all().order_by('price')

    context = {
        "packages": packages
    }

    return render(request, 'base/plans.html', context)


def investment_plans_list(request):
    """Display all active investment plans (public view)"""
    plans = InvestmentPlan.objects.filter(is_active=True)

    context = {
        'plans': plans,
        'title': 'Investment Options',
        'subtitle': 'Structured payouts ensure predictable income and reduced risk exposure'
    }
    return render(request, 'investments/plans_list.html', context)


@login_required
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
    """Handle new investment creation"""
    plan = get_object_or_404(InvestmentPlan, slug=plan_slug, is_active=True)

    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))

        # Validate amount
        if amount < plan.min_amount:
            messages.error(
                request, f"Minimum investment is ₦{plan.min_amount:,.2f}")
            return redirect('investment_detail', slug=plan_slug)

        if plan.max_amount and amount > plan.max_amount:
            messages.error(
                request, f"Maximum investment is ₦{plan.max_amount:,.2f}")
            return redirect('investment_detail', slug=plan_slug)

        # Check for existing pending/active investment
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
        with transaction.atomic():
            investment = Investment.objects.create(
                user=request.user,
                plan=plan,
                amount=amount,
                status=InvestmentStatus.PENDING
            )

            # Create scheduled payouts
            _create_payout_schedule(investment)

        messages.success(
            request,
            f"Investment request created! Reference: {investment.reference_code}. "
            "Please upload payment proof to complete."
        )
        return redirect('upload_payment_proof', investment_id=investment.id)

    return redirect('investment_detail', slug=plan_slug)


def _create_payout_schedule(investment):
    """Create scheduled payouts for an investment"""
    plan = investment.plan
    payout_amount = plan.calculate_payout_amount(investment.amount)
    principal_per_payout = investment.amount / plan.total_payouts
    return_per_payout = (plan.calculate_total_return(
        investment.amount) / plan.total_payouts)

    for i in range(1, plan.total_payouts + 1):
        months_from_start = (i - 1) * plan.payout_frequency_months
        scheduled_date = timezone.now() + timezone.timedelta(days=months_from_start * 30)

        InvestmentPayout.objects.create(
            investment=investment,
            payout_number=i,
            principal_amount=principal_per_payout,
            return_amount=return_per_payout,
            scheduled_date=scheduled_date
        )


@login_required
def upload_payment_proof(request, investment_id):
    """Upload payment proof for pending investment"""
    investment = get_object_or_404(
        Investment,
        id=investment_id,
        user=request.user,
        status=InvestmentStatus.PENDING
    )

    if request.method == 'POST':
        payment_proof = request.FILES.get('payment_proof')

        if not payment_proof:
            messages.error(request, "Please upload a payment proof file.")
            return render(request, 'investments/upload_proof.html', {'investment': investment})

        investment.payment_proof = payment_proof
        investment.save()

        messages.success(
            request,
            "Payment proof uploaded successfully! Your investment is pending verification."
        )
        return redirect('my_investments')

    context = {'investment': investment}
    return render(request, 'investments/upload_proof.html', context)


@login_required
def my_investments(request):
    """List all user's investments"""
    investments = Investment.objects.filter(
        user=request.user).select_related('plan')

    # Calculate totals
    total_invested = sum(inv.amount for inv in investments if inv.status in [
                         'active', 'completed'])
    total_returned = sum(inv.total_paid_out for inv in investments)
    active_count = sum(1 for inv in investments if inv.status == 'active')

    context = {
        'investments': investments,
        'total_invested': total_invested,
        'total_returned': total_returned,
        'active_count': active_count,
    }
    return render(request, 'investments/my_investments.html', context)


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
    active_investment = investments.filter(status=InvestmentStatus.ACTIVE).first()
    
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
    active_investments_count = investments.filter(status=InvestmentStatus.ACTIVE).count()
    total_payouts_received = sum(inv.payouts_completed for inv in investments)
    
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
    available_withdrawal = total_returns_earned  # Adjust based on your withdrawal logic
    
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
        Investment, id=investment_id, status=InvestmentStatus.PENDING)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '')

        if action == 'approve':
            with transaction.atomic():
                investment.status = InvestmentStatus.ACTIVE
                investment.payment_verified_by = request.user
                investment.payment_verified_at = timezone.now()
                investment.admin_notes = notes
                investment.save()  # This triggers start_date and maturity_date calculation

                # Update first payout to processing
                first_payout = investment.payouts.first()
                if first_payout:
                    first_payout.status = InvestmentPayout.PayoutStatus.SCHEDULED
                    first_payout.save()

            messages.success(
                request, f"Investment {investment.reference_code} approved and activated.")

        elif action == 'reject':
            investment.status = InvestmentStatus.CANCELLED
            investment.admin_notes = notes
            investment.save()
            messages.info(
                request, f"Investment {investment.reference_code} rejected.")

        return redirect('admin_investment_list')

    context = {'investment': investment}
    return render(request, 'investments/verify.html', context)


@staff_member_required
def process_payout(request, payout_id):
    """Admin processing of scheduled payout"""
    payout = get_object_or_404(
        InvestmentPayout, id=payout_id, status=InvestmentPayout.PayoutStatus.SCHEDULED)

    if request.method == 'POST':
        with transaction.atomic():
            payout.status = InvestmentPayout.PayoutStatus.COMPLETED
            payout.processed_date = timezone.now()
            payout.payment_method = request.POST.get('payment_method', '')
            payout.payment_reference = request.POST.get(
                'payment_reference', '')
            payout.save()

            # Update investment totals
            investment = payout.investment
            investment.total_paid_out += payout.total_amount
            investment.payouts_completed += 1

            # Check if all payouts completed
            if investment.payouts_completed >= investment.plan.total_payouts:
                investment.status = InvestmentStatus.COMPLETED

            investment.save()

        messages.success(
            request, f"Payout #{payout.payout_number} processed successfully.")
        return redirect('admin_investment_list')

    context = {'payout': payout}
    return render(request, 'investments/process_payout.html', context)


def _404(request, exception):
    return render(request, '404.html', {})
