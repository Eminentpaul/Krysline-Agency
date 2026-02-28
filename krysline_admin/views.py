from django.shortcuts import render, redirect, get_object_or_404
from authentication.models import User, UserProfile
from affiliation.models import AffiliatePackage, Affiliate, PropertyTransaction
from django.contrib.auth.decorators import login_required
from security.decorators import *
from users.models import Withdrawal, Transaction
import base64
from django.db.models import Sum
from django.contrib import messages as mg
from .forms import *
from .models import TransactionPIN
from datetime import datetime
from monnify_verification.monnify_api import *
# Create your views here.


@login_required(login_url="login")
@rate_limit("20/hour")
@log_security_event(action="LOGIN")
def home(request):

    set_pin = False
    if TransactionPIN.objects.filter(user=request.user).exists():
        set_pin = True


    if request.user.user_type != "manager":
        return redirect('dashboard')
    
    if request.method == 'POST':
        pin = request.POST.get('pin')
        cpin = request.POST.get('cpin')

        trans_pin = TransactionPIN()

        if pin == cpin:
            trans_pin.user = request.user
            trans_pin.set_pin(pin)
            return redirect('krysline_admin')
        else:
            mg.error(request, 'PIN, Not matching, Try Again!')
            

    total_income = 0

    total_withdrawl = Withdrawal.objects.all().filter(
        status="approved").aggregate(total=Sum('amount'))['total'] or 0
    pending_withdrawl = Withdrawal.objects.all().filter(
        status="pending").aggregate(total=Sum('amount'))['total'] or 0
    totalPackageIncome = Affiliate.objects.all().filter(
        is_active=True).aggregate(total=Sum("package__price"))['total'] or 0
    totalPropertySale = PropertyTransaction.objects.all().filter(
        is_verified=True).aggregate(total=Sum('amount'))['total'] or 0

    total_income = totalPackageIncome + totalPropertySale

    context = {
        'total_users': User.objects.all().count(),
        'active_users': User.objects.all().filter(is_active=True).count(),
        'unverified_email': User.objects.all().filter(verified_email=False).count(),
        'total_packages': AffiliatePackage.objects.all().filter(is_active=True).count(),
        'total_withdrawal': total_withdrawl,
        'transactions': Transaction.objects.all(),
        'pending_withdrawal': pending_withdrawl,
        'total_income': total_income,
        'basic': AffiliatePackage.objects.all()[0],
        'standard': AffiliatePackage.objects.all()[1],
        'premium': AffiliatePackage.objects.all()[2],
        'professional': AffiliatePackage.objects.all()[3],
        'elite': AffiliatePackage.objects.all()[4],
        'set_pin': set_pin

    }
    return render(request, 'krysline_admin/index.html', context)


@login_required(login_url="login")
@rate_limit("10/minute")
def active_user(request):
    if request.user.user_type != "manager":
        return redirect('dashboard')

    # print()

    context = {
        "active_users": User.objects.all().filter(is_active=True, user_type__in=["affiliate", "secretary"]),
        'active': True
    }

    return render(request, 'krysline_admin/active-user.html', context)


@login_required(login_url="login")
@rate_limit("10/minute")
def inactive_user(request):
    if request.user.user_type not in ["manager", 'admin']:
        return redirect('dashboard')

    # print()

    context = {
        "inactive_users": User.objects.all().filter(is_active=False, user_type__in=["affiliate", "secretary"]),
        'active': False
    }

    return render(request, 'krysline_admin/active-user.html', context)


@login_required(login_url="login")
@rate_limit("10/minute")
@log_security_event(action="PROFILE_UPDATE")
def updateUser(request, pk):
    user = get_object_or_404(User, id=pk)
    error_msg = None

    form = UserUpdateForm(instance=user)

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user)
        if form.is_valid():
            user_type = form.cleaned_data.get('user_type')

            if user_type == 'admin':
                mg.error(request, 'User Cannot be an Admin')
            else:
                form.save()
                mg.success(request, 'User Updated Successfully!')

                return redirect('active_user')
        else:
            errors = form.errors.get_json_data(escape_html=True)
            for error in errors:
                error_msg = errors[error][0]['message']
            mg.error(request, error_msg)

    context = {
        'edit_user': user,
        'form': form
    }
    return render(request, 'krysline_admin/edit-user.html', context)


@login_required(login_url="login")
@rate_limit("10/minute")
@log_security_event(action="USER_DELETE")
def delete_user(request, pk):
    user = get_object_or_404(User, id=pk)
    user.delete()

    mg.success(request, 'Account Deleted successfully!')
    return redirect("active_user")


@login_required(login_url="login")
@rate_limit("5/hour")
@log_security_event(action="TRANSACTION_VIEW")
def transaction_history(request):
    transactions = Transaction.objects.all()

    context = {
        "transactions": transactions,
    }
    return render(request, 'krysline_admin/transaction.html', context)


@login_required(login_url="login")
@rate_limit("5/hour")
@log_security_event(action="WITHDRAWAL_VIEW")
def withdrawal(request):
    withdrawals = Withdrawal.objects.all().filter(status="approved")


    context = {
        'withdrawals': withdrawals,
        'approved': True
    }
    return render(request, 'krysline_admin/withdrawal.html', context)


@login_required(login_url="login")
@rate_limit("50/hour")
@log_security_event(action="WITHDRAWAL_VIEW")
def pending_withdrawal(request):
    pending_withdrawal = Withdrawal.objects.all().filter(status__in= ["pending", "rejected"])
    # print(withdrawals)

    context = {
        'pending_withdrawals': pending_withdrawal,
        'approved': False
    }
    return render(request, 'krysline_admin/withdrawal.html', context)




@login_required(login_url="login")
@rate_limit("500/hour")
@log_security_event(action="WITHDRAWAL_EDIT")
def edit_withdraw(request, trans_id):
    withdrawal = get_object_or_404(Withdrawal, transaction_id=trans_id)
    form = WithdrawUpdateForm(instance=withdrawal)

    bname = '058-Guaranty Trust Bank'
    accnumber = '0570385531'

    # initiate_transfer(accountNumber=accnumber, bankName=bname)
    

     

    if request.method == 'POST':
        form = WithdrawUpdateForm(request.POST, instance=withdrawal)

        if form.is_valid():
            status = form.cleaned_data.get('status')

            if status == 'approved':
                withdraw = form.save(commit=False)
                time_date = datetime.now()

                withdraw.status = status
                withdraw.processed_at = time_date
                withdraw.save()
                

                # TODO: auto transfer integration
                mg.success(request, 'Withdrawal Approved and Paid User Successfully!')
                return redirect('all_pending_withdrawal')

            else: 
                form.save()
                mg.error(request, "'Reject': updated")
    context = {
        'form': form,
        'withdrawal': withdrawal
    }

    return render(request, 'krysline_admin/withdraw-edit.html', context)




@login_required(login_url="login")
@rate_limit("5000/hour")
@log_security_event(action="PACKAGE_UPDATE")
def package_update(request, pk):
    package = get_object_or_404(AffiliatePackage, id=pk)

    form = AffiliatePackageUpdateForm(instance=package)

    if request.method == 'POST':
        form = AffiliatePackageUpdateForm(request.POST, instance=package)

        if form.is_valid():
            name = form.cleaned_data.get('name')
            price = form.cleaned_data.get('price')
            description = form.cleaned_data.get('description')
            has_spillover = form.cleaned_data.get('has_spillover')
            is_active = form.cleaned_data.get('is_active')


            # Updating the Package 
            package.name = name 
            package.price = price
            package.description = description
            package.has_spillover = has_spillover
            package.is_active = is_active

            package.save()

            mg.success(request, "Package Updated Successfully!")
            return redirect('choose_package')
        else:
            errors = form.errors.get_json_data(escape_html=True)
            for error in errors:
                error_msg = errors[error][0]['message']

            mg.error(request, error_msg)



    context = {
        'form': form,
        'package': package, 
    }
    return render(request, 'krysline_admin/package-update.html', context)


def property(request):
    properties = PropertyTransaction.objects.all()

    context = {
        'properties': properties,
    }
    return render(request, 'krysline_admin/properties.html', context)