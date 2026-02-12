from django.contrib.auth import views as auth_views
from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),
    path('verify-sent/', views.verify_email_sent, name='verify_email_sent'),
    path('resend-activation/', views.resend_activation, name='resend_activation'),
    path('logout/', views.logout, name='logout')
] + [
    # 1. Page where user enters email
    path('password-reset/', views.CustomPasswordResetView.as_view(), name='password_reset'),
    
    # 2. Success message after email is sent
    path('password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(template_name='authentication/password_reset_done.html'), 
         name='password_reset_done'),
    
    # 3. The actual reset link from the email
    path('password-reset-confirm/<uidb64>/<token>/', 
         views.CustomPasswordResetConfirmView.as_view(), 
         name='password_reset_confirm'),
    
    # 4. Final success message
    path('password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(template_name='authentication/password_reset_complete.html'), 
         name='password_reset_complete'),
]
