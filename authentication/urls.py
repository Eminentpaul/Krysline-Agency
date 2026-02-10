from django.urls import path
from . import views


urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('activate/<uidb64>/<token>/', views.activate_account, name='activate'),
    path('verify-sent/', views.verify_email_sent, name='verify_email_sent'),
    path('resend-activation/', views.resend_activation, name='resend_activation'),
    path('logout/', views.logout, name='logout')
]
