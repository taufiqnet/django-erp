from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile
from django.utils.html import format_html

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile, Business

class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'is_staff', 'is_active', 'business_display')
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

    def business_display(self, obj):
        if hasattr(obj, 'profile') and obj.profile.business:
            return obj.profile.business.name
        return "N/A"
    business_display.short_description = 'Business'

class UserProfileAdmin(admin.ModelAdmin):
    model = UserProfile
    list_display = ('user', 'user_type', 'business_link', 'allowed_business_type', 'customer_tier')
    list_filter = ('user_type', 'allowed_business_type', 'customer_tier', 'business')
    search_fields = ('user__username', 'user__email', 'business__name')
    raw_id_fields = ('user', 'business')
    autocomplete_fields = ['business']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'user_type')
        }),
        ('Business Information', {
            'fields': ('business', 'allowed_business_type'),
        }),
        ('Customer Information', {
            'fields': ('customer_tier',),
        }),
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj and obj.user_type == 'customer':
            # Hide business fields for customers
            return (
                fieldsets[0],  # User Information
                fieldsets[2]   # Customer Information
            )
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj) or ()
        if obj:
            if obj.user_type == 'vendor':
                readonly_fields += ('customer_tier',)
            elif obj.user_type == 'customer':
                readonly_fields += ('allowed_business_type', 'business')
        return readonly_fields

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "business":
            kwargs["queryset"] = Business.objects.order_by('name')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def business_link(self, obj):
        if obj.business:
            url = f"/admin/your_app/business/{obj.business.id}/change/"
            return format_html('<a href="{}">{}</a>', url, obj.business.name)
        return "N/A"
    business_link.short_description = 'Business'
    business_link.admin_order_field = 'business__name'

# Register the models with the admin site
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
