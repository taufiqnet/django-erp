from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Unit, Product, Contact, Sale, SaleItem, Payment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'parent', 'is_active', 'sort_order', 'description_short')
    list_filter = ('business', 'is_active', 'parent')
    search_fields = ('name', 'business__name', 'description')
    list_editable = ('sort_order', 'is_active')
    list_per_page = 20
    prepopulated_fields = {'meta_title': ('name',)}

    def get_fields(self, request, obj=None):
        fields = [
            'name',
            'business' if request.user.is_superuser else None,
            'parent',
            'description',
            'image',
            'is_active',
            'sort_order',
            'meta_title',
            'meta_description'
        ]
        return [field for field in fields if field is not None]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile') and request.user.profile.business:
            return qs.filter(business=request.user.profile.business)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not obj.business_id and hasattr(request.user, 'profile'):
            obj.business = request.user.profile.business
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj) or [])
        if not request.user.is_superuser and obj:
            readonly_fields.append('business')
        return readonly_fields

    def description_short(self, obj):
        return obj.description[:50] + '...' if obj.description else '-'
    description_short.short_description = 'Description'

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            # Filter categories to show only subcategories (those with a parent)
            kwargs["queryset"] = Category.objects.filter(parent__isnull=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'abbreviation', 'business', 'is_active')
    list_filter = ('business',)
    search_fields = ('name', 'business__name')
    list_per_page = 20

    def get_fields(self, request, obj=None):
        fields = ['name', 'abbreviation', 'description', 'is_active'] 
        if request.user.is_superuser:
            fields.insert(1, 'business')
        return fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile') and request.user.profile.business:
            return qs.filter(business=request.user.profile.business)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not obj.business_id and hasattr(request.user, 'profile'):
            obj.business = request.user.profile.business
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = super().get_readonly_fields(request, obj)
        if not request.user.is_superuser and obj:
            if isinstance(readonly_fields, tuple):
                return readonly_fields + ('business',)
            return list(readonly_fields) + ['business']
        return readonly_fields


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (        
        'name', 
        'image_preview',
        'business', 
        'get_category_display',  # Use custom method for category display
        'sku', 
        'type',
        'cost_price', 
        'original_price',
        'price', 
        'tax_type',
        'tax_rate',
        'unit', 
        'stock_quantity',
        'stock_status',
        'is_active', 
        'is_featured',
        'is_bestseller',
        'is_new',
        'supplier',
        'created_at',
    )
    list_filter = (
        'business', 
        'category', 
        'is_active', 
        'is_featured',
        'is_bestseller',
        'is_new',
        'type',
        'tax_type',
        'stock_status',
        'unit', 
        'supplier',
        'requires_shipping',
        'manage_stock',
    )
    search_fields = (
        'name', 
        'sku', 
        'upc',
        'barcode',
        'description',
        'category__name', 
        'supplier__first_name', 
        'supplier__supplier_business_name'
    )
    list_editable = (
        'cost_price', 
        'original_price', 
        'price', 
        'tax_rate',
        'stock_quantity',
        'is_active',
        'is_featured',
        'is_bestseller',
        'is_new',
    )
    list_per_page = 20
    readonly_fields = (
        'sku', 
        'barcode', 
        'created_at', 
        'updated_at', 
        'created_by', 
        'updated_by',
        'stock_status',
    )
    autocomplete_fields = [
        'category', 
        'unit', 
        'supplier',
        'related_products',
    ]

    def get_fields(self, request, obj=None):
        fields = [
            'name', 'type', 'description', 'short_description',
            'category', 'unit', 'image', 'gallery',
            # Pricing
            'price', 'cost_price', 'original_price', 
            'tax_type', 'tax_rate',
            # Inventory
            'stock_quantity', 'low_stock_threshold', 'manage_stock', 'stock_status',
            'sku', 'barcode', 'upc',
            # Shipping
            'weight', 'height', 'width', 'length', 'requires_shipping',
            # Relations
            'supplier', 'related_products',
            # Status flags
            'is_active', 'is_featured', 'is_bestseller', 'is_new',
            # Metadata
            'meta_title', 'meta_description', 'meta_keywords',
            # Audit
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        
        if request.user.is_superuser:
            fields.insert(0, 'business')
            
        return fields

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile') and request.user.profile.business:
            return qs.filter(business=request.user.profile.business)
        return qs.none()

    def get_category_display(self, obj):
        """Display only the immediate category name without parent hierarchy"""
        return obj.category.name if obj.category else "-"
    get_category_display.short_description = 'Category'
    get_category_display.admin_order_field = 'category__name'  # Enable sorting

    def save_model(self, request, obj, form, change):
        if not obj.business_id and hasattr(request.user, 'profile'):
            obj.business = request.user.profile.business
        
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and obj:
            readonly_fields.append('business')
        return readonly_fields

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit: cover;" />', obj.image.url)
        return '-'
    image_preview.short_description = 'Image Preview'


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'quantity', 'price', 'subtotal')
    list_select_related = ('sale', 'product')
    search_fields = ('sale__invoice_number', 'product__name')
    list_filter = ('product',)
    autocomplete_fields = ('product',)


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number',
        'date',
        'customer',
        'status',
        'payment_status',
        'grand_total',
        'amount_paid',
        'balance_due'
    )
    list_select_related = ('customer', 'business')
    search_fields = ('invoice_number', 'customer__name')
    list_filter = ('status', 'payment_status', 'payment_method', 'date')
    readonly_fields = ('invoice_number', 'balance_due', 'created_at', 'updated_at')
    autocomplete_fields = ('customer',)
    date_hierarchy = 'date'
    ordering = ('-date',)

    fields = (
        'invoice_number',
        'date',
        'customer',
        'status',
        'subtotal',
        'discount_percent',
        'discount_amount',
        'tax_amount',
        'shipping_amount',
        'grand_total',
        'payment_method',
        'payment_status',
        'amount_paid',
        'balance_due',
        'is_due',
        'due_date',
        'shipping_address',
        'shipping_method',
        'tracking_number',
        'customer_note',
        'staff_note',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by'
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile') and request.user.profile.business:
            return qs.filter(business=request.user.profile.business)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        
        if not obj.business_id and hasattr(request.user, 'profile'):
            obj.business = request.user.profile.business
            
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(super().get_readonly_fields(request, obj))
        if not request.user.is_superuser and obj:
            readonly_fields.append('business')
        return readonly_fields


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sale',
        'amount',
        'payment_method',
        'payment_date',
        'status',
        'created_by',
        'created_at'
    )
    list_select_related = ('sale', 'created_by')
    list_filter = (
        'status',
        'payment_method',
        'payment_date',
    )
    search_fields = (
        'sale__invoice_number',
        'amount',
    )
    readonly_fields = (
        'created_at',
        'updated_at',
    )
    date_hierarchy = 'payment_date'
    ordering = ('-payment_date',)

    fields = (
        'sale',
        'amount',
        'payment_method',
        'payment_date',
        'status',
        'notes',
        'created_by',
        'created_at',
        'updated_at',
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if hasattr(request.user, 'profile') and request.user.profile.business:
            return qs.filter(sale__business=request.user.profile.business)
        return qs.none()

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)