from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.home, name='krysline_admin'),
    path('active_user/', views.active_user, name="active_user"),
    path('inactive_user/', views.inactive_user, name="inactive_user"),
    path('edit/<str:pk>/user/', views.updateUser, name='edit_user'),
    path('delete/<str:pk>/user/', views.delete_user, name='delete_user'),
]
