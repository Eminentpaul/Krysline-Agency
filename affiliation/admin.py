# admin.py
from django.contrib import admin
from django.utils import timezone
from .models import PropertyTransaction
from .services import distribute_sale_commissions # The math logic

@admin.register(PropertyTransaction)
class PropertyTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'affiliate', 'amount', 'is_verified']
    actions = ['approve_sales'] # This adds a dropdown menu

    @admin.action(description="Verify selected sales and pay commissions")
    def approve_sales(self, request, queryset):
        for tx in queryset:
            if not tx.is_verified:
                tx.is_verified = True
                tx.verified_by = request.user
                tx.verification_date = timezone.now()
                tx.save()
                
                # Triggers the MLM math
                distribute_sale_commissions(tx)
        
        self.message_user(request, "Selected sales verified and commissions paid.")
