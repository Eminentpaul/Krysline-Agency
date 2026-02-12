from django.urls import path
from . import views


urlpatterns = [
    path("user/", views.dashboard, name='dashboard'),
    path('choose_package/', views.choose_package, name='choose_package'),
    path('payments/', views.payments, name='payments'),
    path('withdraw-fund', views.withdraw_funds, name="withdraw_funds"),
    path('withdraw-history', views.withdraw_history, name="withdraw_history"),
    path('transaction-history', views.transaction_history, name="transaction_history"),
    path('referral-list', views.referral_list, name="referral_list"),
]

