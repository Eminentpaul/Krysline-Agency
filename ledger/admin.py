from django.contrib import admin
from .models import FinancialEntry, Expense
from django.utils.html import format_html

@admin.register(FinancialEntry)
class FinancialEntryAdmin(admin.ModelAdmin):
    list_display = ('reference_id', 'entry_type', 'category', 'amount', 'actor', 'timestamp')
    list_filter = ('entry_type', 'category', 'timestamp')
    search_fields = ('reference_id', 'description', 'actor__email')
    readonly_fields = ('timestamp',) # Cannot edit the time of a transaction



@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):

    list_display = (
        'receipt_number',
        'recorded_by',
        'category',
        'amount',
        'colored_status',
        'created_at',
    )

    list_filter = ('status', 'category', 'created_at')
    search_fields = ('receipt_number', 'description', 'recorded_by__username')
    ordering = ('-created_at',)

    readonly_fields = ('created_at',)

    actions = ['approve_expenses', 'reject_expenses']

    # 🔵 Status Color Badge
    def colored_status(self, obj):
        colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
        }
        return format_html(
            '<span style="color: white; padding:4px 8px; border-radius:6px; background-color:{};">{}</span>',
            colors.get(obj.status, 'gray'),
            obj.status.upper()
        )
    colored_status.short_description = "Status"

    # ✅ Approve Action
    @admin.action(description="Approve selected expenses")
    def approve_expenses(self, request, queryset):
        queryset.update(status='approved')

    # ❌ Reject Action
    @admin.action(description="Reject selected expenses")
    def reject_expenses(self, request, queryset):
        queryset.update(status='rejected')

    # 🔒 Prevent Editing After Approval
    # def get_readonly_fields(self, request, obj=None):
    #     if obj and obj.status == 'approved':
    #         return [field.name for field in self.model._meta.fields]
    #     return super().get_readonly_fields(request, obj)