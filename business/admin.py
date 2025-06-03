from django.contrib import admin
from .models import Business

class BusinessAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = ('name', 'legal_name', 'email', 'contact_number', 'is_active', 'created_at',  'updated_at', )
    
    # Fields that can be searched
    search_fields = ('name', 'legal_name', 'email', 'registration_number', 'tax_id', 'vat_number')
    
    # Fields to filter by in the right sidebar
    list_filter = ('is_active', 'country', 'industry', 'created_at')
    
    # Fields that are read-only in the admin form
    readonly_fields = ('bid', 'created_at', 'updated_at', 'deleted_at', )
    
    # Fieldsets for organizing the form into sections
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'legal_name', 'type', 'business_logo', 'description', 'industry', 'employees_count')
        }),
        ('Registration and Tax Information', {
            'fields': ('registration_number', 'tax_id', 'vat_number')
        }),
        ('Contact Information', {
            'fields': ('contact_number', 'alternate_contact', 'hotline', 'email', 'support_email')
        }),
        ('Address Information', {
            'fields': ('address_line1', 'address_line2', 'billing_address', 'shipping_address', 'state', 'city', 'district', 'division', 'country')
        }),
        ('Social Media Links', {
            'fields': ('website', 'facebook', 'linkedin', 'twitter', 'youtube', 'instagram')
        }),
        ('Financial and Operational Details', {
            'fields': ('currency', 'fiscal_year_start', 'fiscal_year_end', 'timezone')
        }),
        ('Audit Fields', {
            'fields': ('is_active', 'created_at', 'updated_at', 'deleted_at')
        }),
    )
    
    # Automatically populate created_by and updated_by fields
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If the object is being created
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

# Register the Business model with the custom admin class
admin.site.register(Business, BusinessAdmin)