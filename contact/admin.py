from django.contrib import admin
from .models import Contact
from django.utils.html import format_html

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    # Fields to display in the list view
    list_display = (
        'contact_id', 'name', 'type', 'email', 'mobile', 'is_active', 'business', 'created_at', 'created_by', 'updated_at', 'updated_by'
    )
    
    # Fields that can be searched
    search_fields = (
        'first_name', 'last_name', 'email', 'mobile', 'contact_id', 'supplier_business_name'
    )
    
    # Fields to filter by in the right sidebar
    list_filter = (
        'type', 'is_active', 'country', 'created_at', 'updated_at'
    )
    
    # Fields that are read-only in the admin form
    readonly_fields = (
        'cid', 'contact_id', 'created_at', 'updated_at', 'created_by', 'updated_by'
    )
    
    # Fieldsets for organizing the form into sections
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'cid', 'business', 'type', 'prefix', 'first_name', 'middle_name', 'last_name', 
                'email', 'contact_id', 'is_active', 'tax_number', 'supplier_business_name'
            )
        }),
        ('Address Information', {
            'fields': (
                'address_line1', 'address_line2', 'city', 'state', 'country', 
                'zip_code', 'shipping_address'
            )
        }),
        ('Contact Information', {
            'fields': (
                'mobile', 'landline', 'alternate_number'
            )
        }),
        ('Financial Information', {
            'fields': (
                'pay_term_number', 'pay_term_type', 'credit_limit', 'balance'
            )
        }),
        ('Reward Points', {
            'fields': (
                'total_rp', 'total_rp_used', 'total_rp_expired'
            )
        }),
        ('Additional Information', {
            'fields': (
                'dob', 'is_walk_in', 'is_default', 'is_export', 'position', 'customer_group_id'
            )
        }),
        ('Custom Fields', {
            'fields': (
                'custom_field1', 'custom_field2', 'custom_field3', 
                'custom_field4', 'custom_field5'
            )
        }),
        ('Suggested Additions', {
            'fields': (
                'notes', 'tags', 'reference', 'website', 'social_media', 
                'language', 'currency', 'payment_terms'
            )
        }),
        ('Audit Fields', {
            'fields': (
                'created_at', 'updated_at', 'created_by', 'updated_by'
            )
        }),
    )
    
    # Automatically set the user field to the logged-in user
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If the object is being created
            obj.created_by = request.user  # Set the created_by field
        obj.updated_by = request.user  # Always update updated_by field
        super().save_model(request, obj, form, change)
    
    # Custom method to display full name in the list view
    def name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    name.short_description = 'Name'
    
    # Custom method to format the CID field
    def cid(self, obj):
        return format_html(f"<strong>{obj.cid}</strong>")
    cid.short_description = 'Contact ID'