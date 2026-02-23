from django.shortcuts import render, redirect, get_object_or_404
from authentication.models import User, UserProfile
from affiliation.models import AffiliatePackage, Affiliate, PropertyTransaction
from django.contrib.auth.decorators import login_required
from security.decorators import *
from users.models import Withdrawal, Transaction
from django.db.models import Sum
from django.contrib import messages as mg
from .forms import UserUpdateForm

# Create your views here.

@login_required(login_url="login")
@rate_limit("10/minute")
@log_security_event(action="LOGIN")
def home(request):

    if request.user.user_type != "manager":
        return redirect('dashboard')

    total_income = 0

    total_withdrawl = Withdrawal.objects.all().filter(status="approved").aggregate(total=Sum('amount'))['total'] or 0
    pending_withdrawl = Withdrawal.objects.all().filter(status="pending").aggregate(total=Sum('amount'))['total'] or 0
    totalPackageIncome = Affiliate.objects.all().filter(is_active=True).aggregate(total=Sum("package__price"))['total'] or 0
    totalPropertySale = PropertyTransaction.objects.all().filter(is_verified=True).aggregate(total=Sum('amount'))['total'] or 0

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
                mg.success(request,'User Updated Successfully!')

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
