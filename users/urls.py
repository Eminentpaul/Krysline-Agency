from django.urls import path
from . import views


urlpatterns = [
    path("user/", views.user_dashboard, 'secure_dashboard'),
    path('choose_package', views.choose_package, name='choose_package')
]
