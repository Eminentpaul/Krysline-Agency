from django.urls import path
from . import views


urlpatterns = [
    path("user/", views.dashboard, name='dashboard'),
    path('choose_package/', views.choose_package, name='choose_package'),
    path('payments/', views.payments, name='payments'),
    path('courses/', views.courses, name='courses'),
    path('withdraw-fund/', views.withdraw_funds, name="withdraw_funds"),
    path('change-pin/', views.user_pin_change, name="change_pin"),
    path('withdraw-history/', views.withdraw_history, name="withdraw_history"),
    path('transaction-history/', views.transaction_history, name="transaction_history"),
    path('referral-list/', views.referral_list, name="referral_list"),
    path('profile_update/', views.profile_update, name="profile_update"),
    path('payment_update/', views.payment_update, name="payment_update"),
    path('verify_bank_account/', views.verify_bank_account, name="verify_bank_account"),
    path('Package/<str:pk>/payment/', views.package_payment, name="package_payment"),
    path('Free-Package/<str:pk>/payment/', views.free_account_activation, name="free_account"),
    path("notification/<str:pk>/user/", views.notify, name="notify"), 
    path("Read/all/", views.mark_all_as_read, name="mark_all_as_read")
]

