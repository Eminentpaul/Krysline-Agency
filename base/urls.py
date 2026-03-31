from django.urls import path
from . import views


urlpatterns = [
    path("", views.package, name="front_package"),

    # User
    path('investments/dashboard/', views.investment_dashboard, name='investment_dashboard'),
    # path('investments/<slug:plan_slug>/create/', views.create_investment, name='create_investment'),
    path('my-investments/', views.my_investments, name='my_investments'),
    # path('my-investments/<uuid:investment_id>/upload-proof/', views.upload_payment_proof, name='upload_payment_proof'),

    # Public
    path('investments/', views.investment_plans_list, name='investment_plans'),
    # path('investments/<slug:slug>/', views.investment_detail, name='investment_detail'),
    
    
    # # Admin
    # path('admin/investments/', views.admin_investment_list, name='admin_investment_list'),
    # path('admin/investments/<uuid:investment_id>/verify/', views.verify_investment, name='verify_investment'),
    # path('admin/payouts/<uuid:payout_id>/process/', views.process_payout, name='process_payout'),
]

