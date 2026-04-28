# admin.py
from django.contrib import admin
from .models import InvestmentPlan, Investment, InvestmentPayout
from django.utils import timezone
from django.contrib import messages

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


    @admin.action(description="Verify selected sales and pay commissions")
    def record_approved_by(self, request, queryset):
        for tx in queryset:
            if tx.status != 'active':
                tx.payment_verified_by = request.user
                tx.payment_verified_at = timezone.now()
                tx.save()

                # Triggers the MLM math
                

        self.message_user(
            request, "Selected sales verified and commissions paid.")

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
    list_display = ['investment', 'payout_number', 'total_amount', 'scheduled_date', 'status']
    list_filter = ['status', 'scheduled_date']
    actions = ['process_selected_payouts']
    
    def process_selected_payouts(self, request, queryset):
        from django.core.management import call_command
        from io import StringIO
        
        out = StringIO()
        for payout in queryset:
            if payout.status == 'scheduled':
                payout.status = 'completed'
                payout.processed_date = timezone.now()
                payout.save()
                
                # Update investment
                inv = payout.investment
                inv.total_paid_out += payout.total_amount
                inv.payouts_completed += 1
                inv.save()
        
        messages.success(request, f'Processed {queryset.count()} payouts')
    process_selected_payouts.short_description = "Process selected payouts immediately"