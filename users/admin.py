from django.contrib import admin
from .models import Transaction, Withdrawal
from django.utils.html import format_html

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id_short', 'user', 'amount_display', 'transaction_type', 'timestamp']
    list_display_links = ['transaction_id_short', 'user', 'amount_display', 'transaction_type', 'timestamp']
    list_filter = ('transaction_type', 'timestamp')
    search_fields = ('transaction_id', 'user__email', 'description')
    readonly_fields = [f.name for f in Transaction._meta.get_fields()] # Make everything Read-Only

    def has_add_permission(self, request): return False
    
    @admin.display(description='Amount')
    def amount_display(self, obj):
        color = "green" if obj.transaction_type in ['deposit', 'commission', 'package_purchase'] else "red"
        
        # 1. Format the number separately first
        formatted_amount = "{:,.2f}".format(obj.amount)
        
        # 2. Pass the color and the formatted string into format_html
        return format_html(
            '<span style="color: {}; font-weight: bold;">₦{}</span>', 
            color, 
            formatted_amount
        )

    def transaction_id_short(self, obj):
        return f"#{str(obj.transaction_id)[:8].upper()}"

@admin.register(Withdrawal)
class WithdrawalAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'amount', 'status', 'created_at')
    list_filter = ('status',)
    readonly_fields = ('transaction_id', 'created_at')
    raw_id_fields = ('user',)
