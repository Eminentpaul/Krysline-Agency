from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.utils.dateparse import parse_date
from .models import FinancialEntry, Expense
from django.utils.dateparse import parse_date
from datetime import datetime, time
from affiliation.models import AffiliatePackage
from .forms import ExpenseForm, ExpenseAddForm
from django.contrib import messages as mg
from security.decorators import *





@login_required(login_url="login")
@rate_limit("20/hour")
@log_security_event(action="INVENTORY_VIEW")
def inventory_report(request):
    queryset = FinancialEntry.objects.all()

    # 1. TEXT SEARCH
    query = request.GET.get('q')
    if query:
        queryset = queryset.filter(
            Q(reference_id__icontains=query) |
            Q(description__icontains=query)
        )

    # 2. DATE RANGE FILTER
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    if start_date:
        start_date = parse_date(start_date)
        if start_date:
            start_datetime = datetime.combine(start_date, time.min)
            queryset = queryset.filter(timestamp__gte=start_datetime)

    if end_date:
        end_date = parse_date(end_date)
        if end_date:
            end_datetime = datetime.combine(end_date, time.max)
            queryset = queryset.filter(timestamp__lte=end_datetime)

    # 3. CALCULATE STATS
    total_inflow = queryset.filter(entry_type='inflow').aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    total_outflow = queryset.filter(entry_type='outflow').aggregate(
        Sum('amount')
    )['amount__sum'] or 0

    net_balance = total_inflow - total_outflow


    context = {
        'entries': queryset,
        'total_inflow': total_inflow,
        'total_outflow': total_outflow,
        'net_balance': net_balance,
        'basic': AffiliatePackage.objects.all()[0],
        'standard': AffiliatePackage.objects.all()[1],
        'premium': AffiliatePackage.objects.all()[2],
        'professional': AffiliatePackage.objects.all()[3],
        'elite': AffiliatePackage.objects.all()[4],
    }

    return render(request, 'ledger/inventory.html', context)



@login_required(login_url="login")
@rate_limit("10/hour")
@log_security_event(action="VIEW_EXPENSE")
def expenses(request):
    all_expenses = Expense.objects.all()

    context = {
        "all_expenses": all_expenses,
        'all': True
    }
    return render(request, 'ledger/expenses.html', context)



@login_required(login_url="login")
@rate_limit("10/hour")
@log_security_event(action="VIEW_EDIT_EXPENSE")
def view_expense(request, pk):
    expense = get_object_or_404(Expense, id=pk)

    form = ExpenseForm(instance=expense)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, instance=expense)

        if form.is_valid():
            category = form.cleaned_data.get('category')
            amount = form.cleaned_data.get('amount')
            status = form.cleaned_data.get('status')
            description = form.cleaned_data.get('description')

            expense_update = form.save(commit=False)
            expense_update.category = category
            expense_update.amount = amount
            expense_update.status = status
            expense_update.description = description
            expense_update.save()

            if status == 'approved':
                mg.success(request, 'Expense Approved Successfully')
            else: mg.success(request, 'Expense updated successfully')

            return redirect("all_expenses")
        else:
            mg.error(request, 'Invalid input, Try Again')


    context = {
        'form': form,
        'expense': expense,
        'edit': True
    }

    return render(request, 'ledger/edith-expense.html', context)



@login_required(login_url="login")
@rate_limit("10/hour")
@log_security_event(action="ADD_EXPENSE")
def add_expense(request):

    form = ExpenseForm()

    if request.method == 'POST':
        form = ExpenseAddForm(request.POST)

        if form.is_valid():
            category = form.cleaned_data.get('category')
            amount = form.cleaned_data.get('amount')
            description = form.cleaned_data.get('description')

            expense_update = form.save(commit=False)
            expense_update.category = category
            expense_update.amount = amount
            expense_update.description = description
            expense_update.recorded_by = request.user
            expense_update.save()

            
            mg.success(request, 'Expense Added Successfully')
            

            return redirect("all_expenses")
        else:
            errors = form.errors.get_json_data(escape_html=True)
            print(errors) 
            for error in errors:
                error_msg = errors[error][0]['message']
            mg.error(request, error_msg)


    context = {
        'form': form,

    }

    return render(request, 'ledger/edith-expense.html', context)



@login_required(login_url="login")
@rate_limit("10/hour")
@log_security_event(action="APPROVE_EXPENSE")
def approve_expense(request, pk):
    expense = get_object_or_404(Expense, id=pk)
    expense.status = 'approved'
    expense.save()

    
    mg.success(request, 'Expense Approved Successfully')
    return redirect("all_expenses")


@login_required(login_url="login")
@rate_limit("10/hour")
@log_security_event(action="REJECT_EXPENSE")
def reject_expense(request, pk):
    expense = get_object_or_404(Expense, id=pk)
    expense.status = 'rejected'
    expense.save()

    
    mg.info(request, 'Expense Reject Updated Successfully')
    return redirect("all_expenses") 