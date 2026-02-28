from django.http import HttpResponseForbidden
from .models import BlacklistedIP
from django.contrib import messages as mg

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
