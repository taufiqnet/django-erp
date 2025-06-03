from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Unit, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'description_short')
    list_filter = ('business',)
    search_fields = ('name', 'business__name')
    list_per_page = 20

    def description_short(self, obj):
        return obj.description[:50] + '...' if obj.description else '-'
    description_short.short_description = 'Description'


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'business',)
    list_filter = ('business',)
    search_fields = ('name', 'business__name')
    list_per_page = 20

    def description_short(self, obj):
        return obj.description[:50] + '...' if obj.description else '-'
    description_short.short_description = 'Description'

from django.contrib import admin
from django.utils.html import format_html
from .models import Product, ProductVariation


@admin.register(ProductVariation)
class ProductVariationAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_preview', 'product', 'sku', 'price', 'stock_quantity', 'is_active', 'created_at', 'created_by', 'updated_at', 'updated_by')
    list_filter = ('product', 'is_active')
    search_fields = ('name', 'sku', 'product__name')
    readonly_fields = ('sku', 'barcode', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('product', 'name',)
        }),
        ('Pricing', {
            'fields': ('price', 'cost_price', 'original_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'low_stock_threshold', 'is_out_of_stock')
        }),
        ('Details', {
            'fields': ('barcode', 'weight', 'height', 'width', 'length', 'image')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Image Preview'


class ProductVariationInline(admin.TabularInline):
    model = ProductVariation
    extra = 1  # Number of empty forms to display for adding new variations
    fields = ('name', 'original_price', 'price', 'cost_price', 'stock_quantity', 'is_active', 'weight', 'height', 'width', 'length')  # Removed 'sku' from here
    readonly_fields = ('sku',)  # Include 'sku' as read-only
    show_change_link = True

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (        
        'name', 
        'image_preview',
        'business', 
        'category', 
        'sku', 
        'cost_price', 
        'original_price',
        'price', 
        'unit', 
        'stock_quantity', 
        'is_active', 
        'supplier', 
        # 'created_at', 'created_by', 'updated_at', 'updated_by'
    )
    list_filter = ('business', 'category', 'is_active', 'unit', 'supplier')
    search_fields = ('name', 'sku', 'category__name', 'supplier__first_name', 'supplier__supplier_business_name')
    list_editable = ('cost_price', 'original_price', 'price', 'stock_quantity', 'is_active')
    list_per_page = 20
    readonly_fields = ('sku', 'barcode', 'created_at', 'updated_at')  # Include 'sku' here
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'category', 'business', 'unit')
        }),
        ('Pricing and Inventory', {
            'fields': ('price', 'cost_price', 'original_price', 'stock_quantity', 'low_stock_threshold', 'is_out_of_stock')
        }),
        ('Product Identification', {
            'fields': ('barcode', 'upc')
        }),
        ('Supplier Information', {
            'fields': ('supplier',)
        }),
        ('Status and Metadata', {
            'fields': ('is_active', 'is_featured', 'meta_title', 'meta_description', 'keywords')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [ProductVariationInline]  # Add the inline for variations

    # Automatically set the user field to the logged-in user
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # If the object is being created
            obj.created_by = request.user  # Set the created_by field
        obj.updated_by = request.user  # Always update updated_by field
        super().save_model(request, obj, form, change)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Image Preview'

