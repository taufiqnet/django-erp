from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile

# Customize the UserAdmin to include the custom User model
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('bio',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )
    search_fields = ('username', 'email')
    ordering = ('username',)

# Admin customization for UserProfile
class UserProfileAdmin(admin.ModelAdmin):
    model = UserProfile
    list_display = ('user', 'user_type', 'allowed_business_type', 'customer_tier')
    list_filter = ('user_type', 'allowed_business_type', 'customer_tier')
    search_fields = ('user__username', 'user__email')
    raw_id_fields = ('user',)

    # Additional customization
    fieldsets = (
        (None, {
            'fields': ('user', 'user_type', 'allowed_business_type', 'customer_tier')
        }),
    )
    ordering = ('user__username',)

    def get_readonly_fields(self, request, obj=None):
        """
        Make `customer_tier` editable only for customers
        and `allowed_business_type` editable only for vendors.
        """
        readonly_fields = super().get_readonly_fields(request, obj)
        if obj:
            if obj.user_type == 'vendor':
                readonly_fields += ('customer_tier',)
            elif obj.user_type == 'customer':
                readonly_fields += ('allowed_business_type',)
        return readonly_fields

# Register the models with the admin site
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
