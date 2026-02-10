# admin.py
from django.contrib import admin
from django.utils import timezone
from .models import PropertyTransaction, AffiliatePackage, Affiliate
from .services import distribute_commissions # The math logic

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
                distribute_commissions(tx)
        
        self.message_user(request, "Selected sales verified and commissions paid.")




@admin.register(AffiliatePackage)
class AffiliatePackageAdmin(admin.ModelAdmin):
    # Updated to match the fields actually present in your Model
    list_display = (
        'name', 
        'price_formatted', 
        'generations', 
        'is_active', 
        'has_spillover', 
        'created_at'
    )
    
    list_filter = ('is_active', 'has_spillover', 'generations')
    list_display_links = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            # Removed 'description' because it's not in the model
            'fields': ('name', 'price', 'is_active', 'url')
        }),
        ('MLM Structure', {
            'fields': ('generations', 'has_spillover'),
            'description': 'Configure how many levels deep this package earns.'
        }),
        ('Commission Logic', {
            # Use 'commissions' (the JSONField) instead of the old separate gen fields
            'fields': ('commissions',),
            'description': "Enter as JSON. Example: {'1': 20, '2': 10, '3': 5}"
        }),
    )

    @admin.display(description='Price (NGN)')
    def price_formatted(self, obj):
        return f"₦{obj.price:,.2f}"

    def get_readonly_fields(self, request, obj=None):
        if obj and not request.user.is_superuser:
            return ('price', 'generations', 'name')
        return super().get_readonly_fields(request, obj)
    


@admin.register(Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    # 1. Columns shown in the main list
    list_display = (
        'get_email', 
        'referral_code', 
        'get_upline', 
        'package', 
        'is_active', 
        'joined_at'
    )
    
    # 2. Filters on the right sidebar
    list_filter = ('is_active', 'package', 'joined_at')
    
    # 3. Search functionality (Search by email, username, or KAL code)
    search_fields = ('user__email', 'user__username', 'referral_code')
    
    # 4. Security: Prevent manual editing of codes and dates
    readonly_fields = ('referral_code', 'joined_at')
    
    # 5. Searchable dropdown for Upline (Essential for large MLM trees)
    raw_id_fields = ('upline', 'user')

    # 6. Organized layout for the edit page
    fieldsets = (
        ('Account Identity', {
            'fields': ('user', 'referral_code', 'package')
        }),
        ('Business Status', {
            'fields': ('is_active',)
        }),
        ('MLM Tree', {
            'fields': ('upline',),
            'description': 'The Upline is the person who referred this affiliate.'
        }),
        ('System Info', {
            'fields': ('joined_at',),
            'classes': ('collapse',) # Hidden by default
        }),
    )

    # Helper: Show Email from the User model
    @admin.display(description='Email')
    def get_email(self, obj):
        return obj.user.email

    # Helper: Show Upline with their Referral Code
    @admin.display(description='Upline (Referrer)')
    def get_upline(self, obj):
        if obj.upline:
            return f"{obj.upline.user.username} ({obj.upline.referral_code})"
        return "Company (Direct)"

    # Security: Prevent deletion of Affiliates (Deactivate instead)
    # This preserves the financial audit trail
    def has_delete_permission(self, request, obj=None):
        return False 