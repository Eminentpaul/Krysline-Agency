from django.core.cache import cache
from django.utils import timezone
import structlog
from datetime import timedelta
from authentication.models import BlacklistedIP, User  # Assuming User is your custom user


logger = structlog.get_logger(__name__)

def is_ip_blocked(ip_address):
    """
    Checks cache first (fast), then DB (fallback) to see if IP is blocked.
    """
    # 1. Check Cache
    if cache.get(f"block:{ip_address}"):
        return True
    
    # 2. Check Database
    exists = BlacklistedIP.objects.filter(ip_address=ip_address).exists()
    if exists:
        # Re-populate cache for 1 hour so we don't hit DB again
        cache.set(f"block:{ip_address}", True, 3600)
        return True
    
    return False

def increment_failed_attempts(user_email, ip_address):
    """
    Tracks failures and triggers account/IP lockout.
    """
    # Keys for tracking
    user_key = f"failed_user:{user_email}"
    ip_key = f"failed_ip:{ip_address}"

    
    # Increment counts in cache (valid for 30 mins)
    user_failures = cache.get(user_key, 0) + 1
    ip_failures = cache.get(ip_key, 0) + 1
    
    cache.set(user_key, user_failures, 1800)
    cache.set(ip_key, ip_failures, 1800)


    # 1. Lock User Account (if they exist)
    try:
        user = User.objects.get(email=user_email)
        if user_failures >= 5:
            user.profile.account_locked_until = timezone.now() + timedelta(minutes=60)
            user.profile.save()
            # Reset cache so they aren't locked 'forever' via the counter
            cache.delete(user_key)
    except User.DoesNotExist:
        pass

    # 2. Block IP (if IP keeps spamming different usernames)
    if ip_failures >= 5:
        BlacklistedIP.objects.update_or_create(
            ip_address=ip_address, 
            reason="Exceeded 5 failed login attempts in 30 mins"
        )
        logger.warning(f"IP {ip_address} has been blacklisted.")
        cache.set(f"block:{ip_address}", True, 3600)
