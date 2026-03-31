# admin.py
from django.contrib import admin
from .models import InvestmentPlan, Investment, InvestmentPayout

@admin.register(InvestmentPlan)
class InvestmentPlanAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'investment_range_display', 'duration_display',
        'payout_structure_display', 'returns_display', 'is_active'
    ]
    list_filter = ['is_active', 'is_annual_roi']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'description', 'is_active', 'display_order')
        }),
        ('Investment Range', {
            'fields': ('min_amount', 'max_amount')
        }),
        ('Duration & Payouts', {
            'fields': ('duration_months', 'payout_frequency_months', 'total_payouts')
        }),
        ('Returns', {
            'fields': ('roi_percentage', 'is_annual_roi')
        }),
    )

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = [
        'reference_code', 'user', 'plan', 'amount', 'status',
        'investment_date', 'maturity_date', 'progress_percentage'
    ]
    list_filter = ['status', 'plan', 'investment_date']
    search_fields = ['reference_code', 'user__email', 'user__username']
    readonly_fields = ['reference_code', 'total_expected_return', 'next_payout_date']

@admin.register(InvestmentPayout)
class InvestmentPayoutAdmin(admin.ModelAdmin):
    list_display = [
        'investment', 'payout_number', 'total_amount',
        'scheduled_date', 'status'
    ]
    list_filter = ['status', 'scheduled_date']
    actions = ['mark_completed']
    
    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_completed.short_description = "Mark selected payouts as completed"