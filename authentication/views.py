
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.db import transaction
from affiliation.models import Affiliate
from django.utils import timezone
from django.contrib import messages as mg
from .forms import SecureLoginForm, AffiliateRegistrationForm
from security.decorators import rate_limit, get_client_ip, log_security_event, logger
from security.models import SecurityAuditLog
from security.security_utils import *
from .token import email_verification_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

from django.core.mail import EmailMessage
# Email Require
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import User



@rate_limit(rate='5/minute')
def login(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    # TODO RETURN TO DASHBOARD
    
    # Initialize the form 
    form = SecureLoginForm(request.POST or None)
    ip_address = get_client_ip(request)

    username = ""

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data.get('email')
        password = form.cleaned_data.get('password')


        # pre-authentication check (IP blocking)
        if is_ip_blocked(ip_address):
            mg.error(request, 'Access Denied.')
            # return render(request, 'authentication/login.html')


        user = authenticate(email=email, password=password)

        if user is not None:
            profile = user.profile

            # Account Status Check
            if profile.account_locked_until and profile.account_locked_until > timezone.now():
                mg.error(request, 'Account temporarily locked, Try later')
                # return redirect('login')
            
            if not user.is_active:
                mg.error(request, 'Account Disabled')
                # return render(request, 'authenticate/login.html')

            if not user.verified_email:
                return render(request, 'authentication/verify_email_sent.html')


            # Success login 
            auth_login(request, user)
            profile.last_login_ip_address = ip_address
            profile.save()

            username = user.username

            SecurityAuditLog.objects.create(
                user = user,
                action = 'LOGIN_SUCCESS',
                ip_address=ip_address,
                severity="LOW"
            )


            if profile.two_factor_enabled:
                request.session['2fa_verified'] = False
                return
                # TODO "RETURN TO 2FA PAGE"


            match getattr(user, 'user_type', 'default'):
                case 'affiliate':
                    # print("User Dashboard")
                    return redirect('dashboard')

                case 'admin':
                    print('Admin Dashboard')
                    return redirect('/admin')
                # TODO return to admin dashboard

                case _:
                    return redirect('login')
                
        else:
            increment_failed_attempts(username, ip_address)
            mg.error(request, 'Invalid Username or Password')

    return render(request, 'authentication/login.html')





@rate_limit(rate='50/hour')  # Strictly limit account creation per IP
@log_security_event(action='USER_REGISTRATION_ATTEMPT')
def register(request): 
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

            mg.error(request, error_msg)

    return render(request, 'authentication/register.html', {'initial_data': initial_data})




def activate_account(request, uidb64, token):

    try:
         # 1. Decode the bytes
        uid_bytes = urlsafe_base64_decode(uidb64)

        # 2. Convert bytes to string (This is where None usually happens)
        uid = force_str(uid_bytes)
        user = User.objects.get(pk=uid)

    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

        if not user:
            return redirect("resend_activation")

    if user.is_active:
        affiliate = Affiliate.objects.all().filter(user=user).first()
        if affiliate and not affiliate.is_active:
            return redirect('choose_package')
        else: return redirect('dashboard')
    # else: 
    #     return redirect("resend_activation")
    

    if user is not None and email_verification_token.check_token(user, token):
        user.is_active = True
        user.verified_email = True
        user.save()

        new_profile = user.profile
        # 2. Get the code from the session
        ref_code = request.session.get('pending_referrer')
        
        if ref_code:
            try:
                # 3. Search the Affiliate model for the owner of the code
        
                upline_affiliate = Affiliate.objects.get(referral_code=ref_code)
                
                # 4. LINKING POINT: 
                # We point the new profile's 'referrer' to the upline's 'profile'
                new_profile.referrer = upline_affiliate.user.profile
                new_profile.save()

                
                Affiliate.objects.get_or_create(
                    user=user,
                    upline=upline_affiliate,
                    # is_active=False # Stays inactive until they pay for a package
                )
                
            except Affiliate.DoesNotExist:
                # If code is wrong, they just don't have a referrer (Company Direct)
                pass 

        # Log them in automatically after verification
        auth_login(request, user)
        mg.success(request, "Email verified successfully! Now choose your package.")
        return redirect('choose_package')
    else:
        return render(request, 'authentication/activation_invalid.html')
    


@rate_limit(rate='300/hour') # Strict global rate limit per IP
def resend_activation(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        user = User.objects.filter(email=email, is_active=False).first()

        if user:
            # 1. SECURITY: Check if we recently sent an email (2-minute cooldown)
            cache_key = f"resend_lock_{user.id}"
            if cache.get(cache_key):
                mg.warning(request, "Please wait 2 minutes before requesting another link.")
                return redirect('resend_activation')

            # 2. Generate New Link
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = email_verification_token.make_token(user)
            link = f"{request.scheme}://{request.get_host()}/user/activate/{uid}/{token}/"

            # 3. Send Email (Re-use your logic from register_view)
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
            
            # 4. Set the 2-minute lock in cache
            cache.set(cache_key, True, 120) 
            
            mg.success(request, "A new activation link has been sent to your email.")
            return redirect('verify_email_sent')
        
        # 5. SECURITY: If user doesn't exist or is already active, 
        # still show success to prevent "Email Enumeration" (hacking)
        mg.success(request, "If an account exists with that email, a link has been sent.")
        return redirect('verify_email_sent')

    return render(request, 'authentication/resend_form.html')



def verify_email_sent(request):
    """
    Renders the 'Check your inbox' page after a successful registration.
    """
    # Optional: You can check if the user just came from the registration page
    # but usually, a simple render is fine for this informational page.
    return render(request, 'authentication/verify_email_sent.html')





def logout(request):
    if request.user.is_authenticated:
        auth_logout(request)
        return redirect('login')
   



class CustomPasswordResetView(PasswordResetView):
    template_name = 'authentication/password_reset_form.html'
    email_template_name = 'authentication/password_reset_email.txt'
    subject_template_name = 'authentication/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'authentication/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
