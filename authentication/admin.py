from django.contrib import admin
from django.contrib.admin import ModelAdmin
from .models import User, UserProfile

# Register your models here.

class UserAdmin(ModelAdmin):
    list_display = ['first_name', 'last_name', 'user_type', 'is_active']
    list_display_links = ['first_name', 'last_name', 'user_type', 'is_active']


admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)