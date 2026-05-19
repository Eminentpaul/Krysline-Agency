from django.urls import path
from .views import * 

urlpatterns = [
    path('affiliate/list/', AffiliateListView.as_view(), name="affiliate-list"), 
    path('affiliate/<str:pk>/detail/', AffiliateDetail.as_view(), name="affiliatepackage-detail"), 

]
