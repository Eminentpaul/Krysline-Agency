
# from django.contrib import admin
# from django.urls import path, include
# import datetime
# from django.utils import timezone
# from affiliation.models import Affiliate


# urlpatterns = [
#     # Panel URLs (include each panel you installed)
#     path('admin/dj-redis-panel/', include('dj_redis_panel.urls')),
#     path('admin/dj-cache-panel/', include('dj_cache_panel.urls')),
#     path('admin/dj-urls-panel/', include('dj_urls_panel.urls')),
    
#     # Control Room dashboard
#     path('admin/dj-control-room/', include('dj_control_room.urls')),
    
#     path('developer/eminent/account/', admin.site.urls),
#     path('user/', include("authentication.urls")),
#     path('', include("base.urls")),
#     path('Dashboard/', include("users.urls")), 
#     path('monnify/api', include("monnify_verification.urls")),
#     path('kryline/agency/ltd/', include("krysline_admin.urls")),
#     path('ledger/', include("ledger.urls")),
    

#     # 2FA 
#     # path('', include(tf_urls)),
# ]


# # 404 handler
# handler404 = 'base.views._404'


# def check_expiration():
#     today = timezone.localtime(timezone.now()) - datetime.timedelta(minutes=2)
#     # TODO: MINUS 1 HOUR 

#     Affiliate.objects.filter(
#             is_active=True,
#             duration__lt=today
#         ).update(is_active=False) 
    
# check_expiration()




from django.contrib import admin
import datetime
from django.utils import timezone
from affiliation.models import Affiliate
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve


urlpatterns = [
    # Panel URLs (include each panel you installed)
    # path('admin/dj-redis-panel/', include('dj_redis_panel.urls')),
    # path('admin/dj-cache-panel/', include('dj_cache_panel.urls')),
    # path('admin/dj-urls-panel/', include('dj_urls_panel.urls')),
    
    # # Control Room dashboard
    # path('admin/dj-control-room/', include('dj_control_room.urls')),
    
    path('', include('base.urls')),
    path('developer/eminent/account/', admin.site.urls),
    path('user/', include("authentication.urls")),
    path('Dashboard/', include("users.urls")), 
    path('monnify/api', include("monnify_verification.urls")),
    path('kryline/agency/ltd/', include("krysline_admin.urls")),
    path('ledger/', include("ledger.urls")),

    # 2FA 
    # path('', include(tf_urls)),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += [
    # your other paths here
    re_path(r'^media/(?P<path>.*)$', serve,{'document_root': settings.MEDIA_ROOT}),
    re_path(r'^static/(?P<path>.*)$', serve,{'document_root': settings.STATIC_ROOT}),
]


def check_expiration():
    today = timezone.localtime(timezone.now()) - datetime.timedelta(minutes=2)
    # TODO: MINUS 1 HOUR 

    Affiliate.objects.filter(
            is_active=True,
            duration__lt=today
        ).update(is_active=False) 
    
check_expiration()



# 404 handler
handler404 = 'base.views._404'