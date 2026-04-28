from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.home, name='krysline_admin'),
    path('All/Transactions/', views.transaction_history, name='all_transaction'),
    path('All/Withdrawal/approved/', views.withdrawal, name='all_approved_withdrawal'),
    path('All/Withdrawal/pending-or-rejected/', views.pending_withdrawal, name='all_pending_withdrawal'),
    path('active_user/', views.active_user, name="active_user"),
    path('inactive_user/', views.inactive_user, name="inactive_user"),
    path('edit/<str:pk>/user/', views.updateUser, name='edit_user'),
    path('Affiliate/<str:pk>/package/', views.view_user_package, name='view_package'),
    path('delete/<str:pk>/user/', views.delete_user, name='delete_user'),
    path('UnblockPIN/<str:pk>/user/', views.unblock_pin, name='unblock_pin'),
    path('edit/<str:trans_id>/withdrawal/', views.edit_withdraw, name='edit_withdraw'),
    path('edit/<str:pk>/package/', views.package_update, name='package_update'), 
    path('Property/Transactions/', views.property, name="properties"),
    path('Add/Property/Transactions/', views.add_property_transaction, name="add_properties"),
    path('Property/Verified/Transactions/', views.Verified_property, name="verified_property"),
    path('Property/unerified/Transactions/', views.unverified_property, name="unverified_property"),
    path('delete/<str:pk>/property/transaction/', views.delete_property_transaction, name='delete_property'), 
    path('verify/<str:pk>/property/transaction/', views.verify_property_transaction, name='verify_property'),  
    path('investments/list/', views.admin_investment_list, name="admin_investment_list"),
    path('investments/<str:investment_id>/verify/', views.verify_investment, name='verify_investment'),
]
