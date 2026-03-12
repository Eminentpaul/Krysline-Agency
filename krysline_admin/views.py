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
from django.utils import timezone
from affiliation.services import distribute_commissions
from ledger.models import Expense
from django.conf import settings

from django_otp.decorators import otp_required
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

    total_withdrawal = Withdrawal.objects.all().filter(
        status="approved").aggregate(total=Sum('amount'))['total'] or 0
    
    total_expenses = Expense.objects.all().filter(
        status="approved").aggregate(total=Sum('amount'))['total'] or 0
    
    pending_withdrawl = Withdrawal.objects.all().filter(
        status="pending").aggregate(total=Sum('amount'))['total'] or 0
    
    totalPackageIncome = Affiliate.objects.all().filter(
        is_active=True).aggregate(total=Sum("package__price"))['total'] or 0
    
    totalPropertySale = PropertyTransaction.objects.all().filter(
        is_verified=True).aggregate(total=Sum('amount'))['total'] or 0

    outflow = total_withdrawal + total_expenses
    net_balance = totalPackageIncome + totalPropertySale - outflow
    total_income = totalPackageIncome + totalPropertySale 


    context = {
        'total_users': User.objects.all().count(),
        'active_users': User.objects.all().filter(is_active=True).count(),
        'unverified_email': User.objects.all().filter(verified_email=False).count(),
        'total_packages': AffiliatePackage.objects.all().filter(is_active=True).count(),
        'total_withdrawal': total_withdrawal,
        'transactions': Transaction.objects.all(),
        'pending_withdrawal': pending_withdrawl,
        'total_income': total_income,
        'basic': AffiliatePackage.objects.all()[0],
        'standard': AffiliatePackage.objects.all()[1],
        'premium': AffiliatePackage.objects.all()[2],
        'professional': AffiliatePackage.objects.all()[3],
        'elite': AffiliatePackage.objects.all()[4],
        'set_pin': set_pin,
        'totalPackageIncome': totalPackageIncome,
        'totalPropertySale': totalPropertySale,
        'total_property': PropertyTransaction.objects.all().count(),
        'outflow': outflow,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
    }
    return render(request, 'krysline_admin/index.html', context)


@login_required(login_url="login")
@rate_limit("1000/hour")
@log_security_event(action="USER_PACKAGE_VIEW")
def view_user_package(request, pk):
    if request.user.user_type != "manager":
        return redirect('dashboard')
    

    affiliate = get_object_or_404(Affiliate, id=pk)
    form = AffilliateForm(instance=affiliate)
    duration = settings.DURATION

    if request.method == 'POST':
        form = AffilliateForm(request.POST, instance=affiliate)
        if form.is_valid():
            active = form.cleaned_data.get('is_active')

            update_affiliate = form.save(commit=False)
            update_affiliate.is_active = active
            update_affiliate.duration = duration
            update_affiliate.save()

            mg.success(request, 'User Package Updated Successfully!')
            return redirect('active_user')
        else:
            mg.error(request, 'Not Updated!')

    context = {
        'form': form,
        'affiliate': affiliate
    }
    return render(request, 'krysline_admin/user-package.html', context)


@login_required(login_url="login")
@rate_limit("10/hour")
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
@rate_limit("10/hour")
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
@rate_limit("10/hour")
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
@rate_limit("10/hour")
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
    pending_withdrawal = Withdrawal.objects.all().filter(
        status__in=["pending", "rejected"])
    # print(withdrawals)

    context = {
        'pending_withdrawals': pending_withdrawal,
        'approved': False
    }
    return render(request, 'krysline_admin/withdrawal.html', context)


@login_required(login_url="login")
@rate_limit("50/hour")
@log_security_event(action="WITHDRAWAL_EDIT")
def edit_withdraw(request, trans_id):
    withdrawal = get_object_or_404(Withdrawal, transaction_id=trans_id)
    form = WithdrawUpdateForm(instance=withdrawal)

    bname = '999992-OPay Digital Services Limited (OPay)'
    accnumber = '8143122946'

    initiate_transfer(accountNumber=accnumber, bankName=bname) 

    # code = get_bank_code(bank_name=bname)
    # print(code)


    # bank = bank_verification(accountNumber=accnumber, bankName=bname)
    # print(bank) 

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
                mg.success(
                    request, 'Withdrawal Approved and Paid User Successfully!')
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
@rate_limit("20/hour")
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


@login_required(login_url="login")
@rate_limit("50/hour")
@log_security_event(action="VIEW_PROPERTY_TRANSACTION")
def property(request):
    properties = PropertyTransaction.objects.all()

    context = {
        'properties': properties,
    }
    return render(request, 'krysline_admin/properties.html', context)


@login_required(login_url="login")
@rate_limit("50/hour")
@log_security_event(action="VIEW_PROPERTY_TRANSACTION")
def Verified_property(request):
    properties = PropertyTransaction.objects.all().filter(is_verified=True)

    context = {
        'verified_properties': properties,
    }
    return render(request, 'krysline_admin/properties.html', context)


@login_required(login_url="login")
@rate_limit("50/hour")
@log_security_event(action="VIEW_PROPERTY_TRANSACTION")
def unverified_property(request):
    properties = PropertyTransaction.objects.all().filter(is_verified=False)

    context = {
        'unverified_properties': properties,
    }
    return render(request, 'krysline_admin/properties.html', context)



@login_required(login_url="login")
@rate_limit("50/hour")
@log_security_event(action="CREATE_PROPERTY_TRANSACTION")
def add_property_transaction(request):
    form = PropertyTransactionForm()
    affiliates = Affiliate.objects.all()

    if request.method == 'POST':
        form = PropertyTransactionForm(request.POST)
        affiliate = request.POST.get('affiliate').split(" ")[-1]
        affiliate_code = affiliate[1:-1]
        try:
            affiliate_user = Affiliate.objects.get(referral_code=affiliate_code) 
            if form.is_valid():
                amount = form.cleaned_data.get('amount')
                transaction_type = form.cleaned_data.get('transaction_type')
                description = form.cleaned_data.get('description')
                client_name = form.cleaned_data.get('client_name')

                new_property = form.save(commit=False) 
                new_property.amount = amount
                new_property.affiliate = affiliate_user
                new_property.transaction_type = transaction_type
                new_property.description = description
                new_property.client_name = client_name
                new_property.save()
                

                mg.success(request, f"{new_property.transaction_id} has been created successfully!")
                return redirect("properties")
                
            else:
                errors = form.errors.get_json_data(escape_html=True)
                for error in errors:
                    error_msg = errors[error][0]['message']

                mg.error(request, error_msg)
        except Affiliate.DoesNotExist:
            mg.error(request, "Affiliate Agent Does not exist") 
            # return redirect('add_properties')


    context = {
        'form': form,
        "affiliates": affiliates,
    }
    return render(request, 'krysline_admin/property-transaction.html', context)


@login_required(login_url="login")
@rate_limit("50/hour")
@log_security_event(action="DELETE_PROPERTY_TRANSACTION")
def delete_property_transaction(request, pk):
    property = get_object_or_404(PropertyTransaction, id=pk)
    property_name = str(property.transaction_id)
    property.delete()

    mg.warning(request, f"{property_name} has been successfully deleted!")
    return redirect('properties')


@login_required(login_url="login")
@rate_limit("50/hour")
@log_security_event(action="VERIFY_APPROVE_PROPERTY_TRANSACTION")
def verify_property_transaction(request, pk):
    property = get_object_or_404(PropertyTransaction, id=pk)
    property_name = str(property.transaction_id)

    with transaction.atomic():
        property.is_verified = True
        property.verified_by = request.user
        property.verification_date = timezone.now()
        property.save()

        distribute_commissions(property=property)

        mg.success(request, f"{property_name} has been successfully Verfied!")
        return redirect('properties')
