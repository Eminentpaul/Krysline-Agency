
from django.contrib import admin
from django.urls import path, include
import datetime
from django.utils import timezone
from affiliation.models import Affiliate


urlpatterns = [
    # Panel URLs (include each panel you installed)
    path('admin/dj-redis-panel/', include('dj_redis_panel.urls')),
    path('admin/dj-cache-panel/', include('dj_cache_panel.urls')),
    path('admin/dj-urls-panel/', include('dj_urls_panel.urls')),
    
    # Control Room dashboard
    path('admin/dj-control-room/', include('dj_control_room.urls')),
    
    path('developer/eminent/account/', admin.site.urls),
    path('user/', include("authentication.urls")),
    path('Dashboard/', include("users.urls")), 
    path('monnify/api', include("monnify_verification.urls")),
    path('kryline/agency/ltd/', include("krysline_admin.urls")),
    path('ledger/', include("ledger.urls")),

    # 2FA 
    # path('', include(tf_urls)),
]


def check_expiration():
    today = timezone.localtime(timezone.now()) - datetime.timedelta(minutes=2)
    # TODO: MINUS 1 HOUR 

    Affiliate.objects.filter(
            is_active=True,
            duration__lt=today
        ).update(is_active=False) 
    
check_expiration()