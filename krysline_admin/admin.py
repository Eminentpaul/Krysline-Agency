from django.contrib import admin
from .models import TransactionPIN
from ledger.models import Expense
from django.utils.html import format_html

# Register your models here.

@admin.register(TransactionPIN)
class TransactionPINAdmin(admin.ModelAdmin):
    list_display = ('user', 'failed_attempts', 'is_locked', 'last_attempt')
    list_filter = ('is_locked',)
    readonly_fields = ('pin_hash', 'created_at') # Safety first
    actions = ['unlock_pins']

    @admin.action(description="Unlock selected user PINs")
    def unlock_pins(self, request, queryset):
        queryset.update(is_locked=False, failed_attempts=0)
        self.message_user(request, "Selected PINs have been unlocked.")




