# import structlog
# from django.core.cache import cache
# from django.http import JsonResponse, HttpResponseForbidden
# from django.contrib.auth.decorators import user_passes_test, login_required
# from django.views.decorators.http import require_http_methods
# from django.views.decorators.csrf import csrf_protect
# from functools import wraps
# import hashlib
# import json
# from datetime import timedelta, datetime


# logger = structlog.get_logger(__name__)


# def rate_limit(rate='100/hour', key_func=None):
#     def decorator(view_func):
#         @wraps(view_func)
#         def wrapped_view(request, *args, **kwargs):
#             # 1. Better IP detection for production
#             ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR')).split(',')[0]
            
#             if key_func:
#                 key = key_func(request)
#             else: 
#                 key = f"rate_limit:{ip}:{view_func.__name__}"

#             # 2. Match Case is clean! (Added 's' support for 'minutes')
#             try:
#                 num_requests_str, period = rate.split('/')
#                 num_requests = int(num_requests_str)

#                 match period.strip().lower():
#                     case "second": time_window = 1
#                     case "minute" | "minutes": time_window = 60
#                     case "hour": time_window = 3600
#                     case "day": time_window = 86400
#                     case _: time_window = 3600
#             except (ValueError, AttributeError):
#                 num_requests, time_window = 100, 3600

#             # 3. Improved Cache Logic
#             current = cache.get(key)
            
#             if current is not None and current >= num_requests:
#                 logger.warning("rate_limit_exceeded", ip=ip, view=view_func.__name__)
#                 return JsonResponse({
#                     'error': "Too many attempts. Please slow down.",
#                     'retry_after_seconds': cache.ttl(key) # Shows actual remaining time
#                 }, status=429)
            
#             # 4. Atomic Increment (Prevents Race Conditions)
#             if current is None:
#                 cache.set(key, 1, timeout=time_window)
#             else:
#                 # Use incr to avoid getting and setting (Race Condition)
#                 cache.incr(key)

#             return view_func(request, *args, **kwargs)
#         return wrapped_view
#     return decorator


# def two_factor_required(view_func):
#     """
#     Docstring for two_factor_required
    
#     :param view_func: Description

#     Require 2FA for sensitive operations
#     """


#     @wraps(view_func)
#     def wrapper(request, *args, **kwargs):
#         if not request.user.is_authenticated:
#             return JsonResponse({
#                 'error': "Authentication required",
#             }, status=401)
        
#         # Check if 2FA is enabled and verified 
#         if hasattr(request.user, 'profile'):
#             if request.user.profile.two_factor_enabled:
#                 if not request.session.get('2fa_verified', False):
#                     return JsonResponse(
#                         {
#                             'error': "Two-factor authentication required",

#                             'redirect': '/verify-2fa/'
#                         }, status = 403
#                     )
#         return view_func(request, *args, **kwargs)
#     return wrapper




import json
import structlog
from functools import wraps
from django.db import transaction
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.timezone import now

logger = structlog.get_logger(__name__)

def get_client_ip(request):
    """Securely fetch the real user IP, even behind a proxy/load balancer."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def rate_limit(rate='100/hour', key_func=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            ip = get_client_ip(request)
            key = key_func(request) if key_func else f"rl:{ip}:{view_func.__name__}"
            
            try:
                num_reqs_str, period = rate.split('/')
                num_requests = int(num_reqs_str)
                # Match Case for clean period parsing
                match period.strip().lower():
                    case 'second': time_window = 1
                    case 'minute': time_window = 60
                    case 'hour':   time_window = 3600
                    case 'day':    time_window = 86400
                    case _:        time_window = 3600
            except (ValueError, AttributeError):
                num_requests, time_window = 100, 3600

            # Atomic increment: Prevents the 'reset bug'
            # .incr() returns the new value; if key doesn't exist, it raises ValueError in some backends
            # so we use a safer pattern:
            if cache.get(key) is None:
                cache.set(key, 1, timeout=time_window)
                current = 1
            else:
                current = cache.incr(key)

            if current > num_requests:
                logger.warning("rate_limit_exceeded", ip=ip, view=view_func.__name__)
                return JsonResponse({
                    'error': 'Too many requests. Please try again later.',
                    'retry_after': f"{cache.ttl(key)}s"
                }, status=429)
            
            return view_func(request, *args, **kwargs)
        return wrapped_view
    return decorator

def two_factor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'error': 'Authentication required'}, status=401)
        
        profile = getattr(request.user, 'profile', None)
        # If user has 2FA enabled but hasn't verified this session
        if profile and profile.two_factor_enabled:
            if not request.session.get('2fa_verified', False):
                return JsonResponse({
                    'error': '2FA verification required',
                    'redirect': '/auth/2fa/verify/'
                }, status=403)
        return view_func(request, *args, **kwargs)
    return wrapper

def validate_request_data(required_fields=None, max_lengths=None):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if request.method in ['POST', 'PUT', 'PATCH']:
                try:
                    # Support both Form-data and JSON payloads
                    if request.content_type == 'application/json':
                        data = json.loads(request.body)
                    else:
                        data = request.POST

                    if required_fields:
                        missing = [f for f in required_fields if f not in data or not str(data[f]).strip()]
                        if missing:
                            return JsonResponse({'error': f'Missing: {", ".join(missing)}'}, status=400)

                    if max_lengths:
                        for field, length in max_lengths.items():
                            if field in data and len(str(data[field])) > length:
                                return JsonResponse({'error': f'{field} is too long'}, status=400)
                except json.JSONDecodeError:
                    return JsonResponse({'error': 'Invalid JSON body'}, status=400)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def log_security_event(action, severity='LOW'):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Using transaction.atomic to ensure the log is saved even if something else fails
            from .models import SecurityAuditLog
            
            response = view_func(request, *args, **kwargs)
            
            # Use on_commit or just create to track the event
            if request.user.is_authenticated:
                SecurityAuditLog.objects.create(
                    user=request.user,
                    action=action,
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:255],
                    details={'path': request.path, 'status': response.status_code},
                    severity=severity
                )
            return response
        return wrapper
    return decorator
