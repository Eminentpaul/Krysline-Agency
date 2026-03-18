from django.http import HttpResponseForbidden
from .models import BlacklistedIP
from django.contrib import messages as mg

import logging
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.contrib.auth import logout
from datetime import timedelta
from django.conf import settings
from django.contrib import messages

class IPBlacklistMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Get the visitor's IP
        ip = request.META.get('REMOTE_ADDR')
        
        # 2. Check if it exists in your BlacklistedIP model
        if BlacklistedIP.objects.filter(ip_address=ip).exists():
            mg.error(request, "403 Forbidden, Your IP has been blacklisted for security reasons. Contact KAL Support.")
        
        return self.get_response(request)




logger = logging.getLogger(__name__)

class IdleTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.idle_timeout = timedelta(minutes=getattr(settings, 'IDLE_TIMEOUT_MINUTES', 30))

    def __call__(self, request):
        if not request.user.is_authenticated or self._is_exempt_path(request.path):
            return self.get_response(request)

        last_activity = request.session.get('last_activity')
        now = timezone.now()

        if last_activity:
            try:
                last_activity_time = parse_datetime(last_activity)
                
                if last_activity_time is None:
                    raise ValueError("Failed to parse datetime")
                
                # Make timezone-aware if needed
                if timezone.is_naive(last_activity_time):
                    last_activity_time = timezone.make_aware(last_activity_time)
                
                idle_duration = now - last_activity_time
                
                if idle_duration > self.idle_timeout:
                    logger.info(f"User {request.user} logged out due to {idle_duration} inactivity")
                    logout(request)
                    request.session.flush()
                    messages.warning(request, "You were logged out due to inactivity.")
                    from django.shortcuts import redirect
                    return redirect('login')
                    
            except (ValueError, TypeError) as e:
                logger.error(f"Error parsing last_activity: {e}")

        # Update last activity
        request.session['last_activity'] = now.isoformat()
        request.session.modified = True

        return self.get_response(request)
    
    def _is_exempt_path(self, path):
        exempt_prefixes = ['/api/', '/keep-alive/', '/static/', '/media/']
        return any(path.startswith(prefix) for prefix in exempt_prefixes)