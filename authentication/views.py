
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.db import transaction
from django.utils import timezone
from django.contrib import messages
from .forms import SecureLoginForm, AffiliateRegistrationForm
from security.decorators import rate_limit, get_client_ip, log_security_event, logger
from security.models import SecurityAuditLog
from security.security_utils import *
from .token import email_verification_token
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import EmailMessage



@rate_limit(rate='5/minute')
def login(request):
    if request.user.is_authenticated:
        return 
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
            messages.error(request, 'Access Denied.')
            # return render(request, 'authentication/login.html')


        user = authenticate(email=email, password=password)

        if user is not None:
            profile = user.profile

            # Account Status Check
            if profile.account_locked_until and profile.account_locked_until > timezone.now():
                messages.error(request, 'Account temporarily locked, Try later')
                # return redirect('login')
            
            if not user.is_active:
                messages.error(request, 'Account Disabled')
                # return render(request, 'authenticate/login.html')


            # Success login 
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
                    print("User Dashboard")
                    return
                # TODO return to user dasboard
                case 'admin':
                    print('Admin Dashboard')
                    return
                # TODO return to admin dashboard

                case _:
                    return redirect('login')
                
        else:
            increment_failed_attempts(username, ip_address)
            messages.error(request, 'Invalid Username or Password')

    return render(request, 'authentication/login.html')





@rate_limit(rate='5/hour')  # Strictly limit account creation per IP
@log_security_event(action='USER_REGISTRATION_ATTEMPT')
def register_view(request):
    if request.user.is_authenticated:
        return redirect('secure_dashboard')

    if request.method == 'POST':
        form = AffiliateRegistrationForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Save user (password is hashed automatically by the form)
                    user = form.save()

                    # Generate Verification Link
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = email_verification_token.make_token(user)
                    link = f"{request.scheme}://{request.get_host()}/activate/{uid}/{token}/"

                    # Send Email
                    subject = "Verify your KAL Affiliate Account"
                    message = render_to_string('authentication/acc_active_email.html', {
                        'user': user,
                        'domain': request.get_host(),
                        'link': link,
                    })
                    email = EmailMessage(subject, message, to=[user.email])
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
        # Pre-fill referral code from URL if present (e.g., /register/?ref=KAL123)
        initial_data = {'referrer_code': request.GET.get('ref', '')}
        form = AffiliateRegistrationForm(initial=initial_data)

    return render(request, 'authentication/register.html', {'form': form})
# TODO: update the template 



def activate_account(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and email_verification_token.check_token(user, token):
        user.is_active = True
        user.save()
        # Log them in automatically after verification
        login(request, user)
        messages.success(request, "Email verified successfully! Now choose your package.")
        return redirect('choose_package')
    else:
        return render(request, 'authentication/activation_invalid.html')
    


@rate_limit(rate='3/hour') # Strict global rate limit per IP
def resend_activation(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        user = User.objects.filter(email=email, is_active=False).first()

        if user:
            # 1. SECURITY: Check if we recently sent an email (2-minute cooldown)
            cache_key = f"resend_lock_{user.id}"
            if cache.get(cache_key):
                messages.warning(request, "Please wait 2 minutes before requesting another link.")
                return redirect('resend_activation')

            # 2. Generate New Link
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = email_verification_token.make_token(user)
            link = f"{request.scheme}://{request.get_host()}/activate/{uid}/{token}/"

            # 3. Send Email (Re-use your logic from register_view)
            # ... [Email sending code here] ...

            # 4. Set the 2-minute lock in cache
            cache.set(cache_key, True, 120) 
            
            messages.success(request, "A new activation link has been sent to your email.")
            return redirect('verify_email_sent')
        
        # 5. SECURITY: If user doesn't exist or is already active, 
        # still show success to prevent "Email Enumeration" (hacking)
        messages.success(request, "If an account exists with that email, a link has been sent.")
        return redirect('verify_email_sent')

    return render(request, 'authentication/resend_form.html')



def verify_email_sent(request):
    """
    Renders the 'Check your inbox' page after a successful registration.
    """
    # Optional: You can check if the user just came from the registration page
    # but usually, a simple render is fine for this informational page.
    return render(request, 'authentication/verify_email_sent.html')

