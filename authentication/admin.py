from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile

# Register your models here.

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    # 1. Columns shown in the main list
    list_display = (
        'email', 
        'username', 
        'first_name', 
        'last_name', 
        'user_type', 
        'is_active', 
        'verified_email'
    )
    
    # 2. Filters for quick sorting
    list_filter = ('user_type', 'is_active', 'verified_email', 'is_staff')
    
    # 3. Search functionality
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('email',)

    # 4. Fieldsets for the Edit Page (Organised for KAL Security)
    fieldsets = (
        ('Account Credentials', {'fields': ('email', 'username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('User Role & Status', {
            'fields': ('user_type', 'is_active', 'verified_email')
        }),
        ('Permissions', {
            'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    # 5. Fieldsets for the 'Add User' Page
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'first_name', 'last_name', 'password', 'user_type'),
        }),
    )

    # Security: Ensure full name shows up correctly in Admin
    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    get_full_name.short_description = 'Full Name'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    # 1. Main List Columns
    list_display = (
        'user_email', 
        'kyc_verified', 
        'two_factor_enabled', 
        'get_balance', 
        'account_status', 
        'last_login_ip_address'
    )
    
    # 2. Sidebar Filters
    list_filter = ('kyc_verified', 'two_factor_enabled', 'account_locked_until')
    
    # 3. Search (Search by user email or username)
    search_fields = ('user__email', 'user__username', 'last_login_ip_address')
    
    # 4. Security: Fields that should NOT be edited manually
    readonly_fields = ('failed_login_attempts', 'last_login_ip_address', 'account_number', 'account_name', 'bank')

    # 5. Grouped Layout
    fieldsets = (
        ('Account Identity', {
            'fields': ('user', 'referrer')
        }),
        ('Financials', {
            'fields': ('balance', 'account_number', 'account_name', 'bank')
        }),
        ('Security & 2FA', {
            'fields': ('two_factor_enabled', 'two_factor_secret', 'failed_login_attempts', 'account_locked_until')
        }),
        ('KYC Verification', {
            'fields': ('kyc_verified', 'kyc_document_type', 'kyc_document_number', 'kyc_verified_at', 'verified_by'),
            'description': 'Ensure documents are physically verified before ticking KYC Verified.'
        }),
        ('Network Info', {
            'fields': ('last_login_ip_address',),
            'classes': ('collapse',)
        }),
    )

    # --- Helper Methods ---

    @admin.display(description='Email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Balance (₦)')
    def get_balance(self, obj):
        return f"₦{obj.balance:,.2f}"

    @admin.display(description='Status')
    def account_status(self, obj):
        from django.utils import timezone
        if obj.account_locked_until and obj.account_locked_until > timezone.now():
            return "❌ LOCKED"
        return "✅ ACTIVE"

    # Security: Use raw_id_fields for the User and Referrer to handle large databases
    raw_id_fields = ('user', 'referrer')



