from django.urls import path
from . import views


urlpatterns = [
    path("", views.inventory_report, name="inventory_report"),
    path('expenses/', views.expenses, name="all_expenses"),
    path('expenses/add/', views.add_expense, name="add_expense"),
    path('view/<str:pk>/expense', views.view_expense, name="view_expense"),
    path('approve/<str:pk>/expense', views.approve_expense, name="approve_expense"),
    path('reject/<str:pk>/expense', views.reject_expense, name="reject_expense"),
]
