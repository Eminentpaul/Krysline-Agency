from django.urls import path
from . import views


urlpatterns = [
    path("user/", views.dashboard, name='dashboard'),
    path('choose_package/', views.choose_package, name='choose_package'),
    path('payments/', views.payments, name='payments'),
]

