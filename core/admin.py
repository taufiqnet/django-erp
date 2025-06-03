from django.contrib import admin
from .models import Category, Vendor, Brand, Unit, Product, ProductImage, CartOrder, CartOrderItems
from .models import ProductReview, Wishlist, ShippingMethod, PaymentMethod, ShippingAddress
from django.utils.html import mark_safe
from django.conf import settings
from import_export.admin import ImportExportModelAdmin
from import_export.formats.base_formats import XLSX, CSV

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'parent', 'category_image', 'category_icon', 'business_type', 'created_at')
    list_filter = ('parent',)
    search_fields = ('title',)
    readonly_fields = ('category_image_preview','category_icon_preview',)  # Make the image preview read-only

    def category_image_preview(self, obj):
        """Display the vendor image in the admin panel."""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" />')
        return "No Image Available"

    category_image_preview.short_description = "Image Preview"

    def category_icon_preview(self, obj):
        """Display the vendor image in the admin panel."""
        if obj.icon:
            return mark_safe(f'<img src="{obj.icon.url}" width="50" height="50" />')
        return "No Icon Available"

    category_icon_preview.short_description = "Icon Preview"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_profile = request.user.userprofile
        return qs.filter(business_type=user_profile.allowed_business_type)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('title', 'business_type', 'address', 'contact', 'chat_resp_time', 'vendor_image_preview', 'user',)  # Fields to display in the list view
    list_filter = ('user',)  # Add filters for better searching
    search_fields = ('title', 'user__username', 'address', 'contact')  # Fields to search within
    readonly_fields = ('vendor_image_preview',)  # Make the image preview read-only
    fieldsets = (
        (None, {
            'fields': ('business_type', 'title', 'image', 'vendor_image_preview', 'description', 'address', 'contact')
        }),
        ('Performance Metrics', {
            'fields': ('chat_resp_time', 'shipping_on_time', 'authentic_rating', 'days_return', 'warranty_period')
        }),
    )

    def vendor_image_preview(self, obj):
        """Display the vendor image in the admin panel."""
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="50" height="50" />')
        return "No Image Available"

    vendor_image_preview.short_description = "Image Preview"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_profile = request.user.userprofile
        return qs.filter(business_type=user_profile.allowed_business_type)


@admin.register(Brand)
class BrandAdmin(ImportExportModelAdmin):
    # Specify which formats to allow
    formats = [XLSX, CSV]

    # Fields to include in import/export
    fields = ('business_type', 'title', 'image', 'description', 'status',)

    # Admin display settings
    list_display = ('title', 'business_type', 'brand_image', 'render_description', 'status', 'created_at')
    search_fields = ('title',)
    list_filter = ('status',)
    ordering = ('-created_at',)

    def render_description(self, obj):
        """
        Safely render the description field as HTML. 
        Fallback to a placeholder if the field is empty.
        """
        if obj.description:
            return mark_safe(obj.description)
        return "No description available"

    render_description.short_description = "Description"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_profile = request.user.userprofile
        return qs.filter(business_type=user_profile.allowed_business_type)


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'short_title', 'created_at')


class ProductImageAdmin(admin.TabularInline):
    model = ProductImage

from django.utils.text import Truncator

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    # Specify which formats to allow
    formats = [XLSX, CSV]

    inlines = [ProductImageAdmin]
    list_display = ['short_title', 'product_image', 'price', 'category', 'business_type', 'featured', 'product_status', 'status', 'brand', 'user']
    list_filter = ('business_type', 'title', 'category', 'product_status', 'brand')
    search_fields = ('title',)

    list_editable = ('featured', 'price', 'product_status', 'status',)
    # Set the number of products to display per page
    list_per_page = 25


    def short_title(self, obj):
        """Truncates the product title to a maximum of 40 characters with ellipsis (...)"""
        return Truncator(obj.title).chars(40)

    short_title.short_description = 'Title'  # Set a descriptive name for the column header

    def save_model(self, request, obj, form, change):
        # Automatically set the user field to the currently logged-in user
        if not change or not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            # Filter categories to show only subcategories (those with a parent)
            kwargs["queryset"] = Category.objects.filter(parent__isnull=False)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        user_profile = request.user.userprofile
        return qs.filter(category__business_type=user_profile.allowed_business_type)

# @admin.register(CartOrder)
# class CartOrderAdmin(admin.ModelAdmin):
#     list_display = ['user', 'price', 'paid_status', 'order_date', 'product_status']





from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import CartOrderItems

@admin.register(CartOrderItems)
class CartOrderItemsAdmin(admin.ModelAdmin):
    list_display = ['order', 'invoice_no', 'order_image', 'item', 'qty', 'price', 'total', 'product_status']
    readonly_fields = ['invoice_no', 'image', 'order_image']
    list_editable = ['product_status',]
    
    # You can make product_status a dropdown in the admin to allow selection
    list_filter = ['product_status']  # Allows filtering by status
    search_fields = ['item', 'product_status']  # Allow search by item and product status
    
    # Enable bulk actions for updating the status
    actions = ['mark_as_processing', 'mark_as_shipped', 'mark_as_delivered', 'mark_as_cancelled', 'mark_as_on_hold']
    
    def mark_as_processing(self, request, queryset):
        """Set selected items as processing."""
        queryset.update(product_status='processing')
        self.message_user(request, "Selected items marked as processing.")
    
    def mark_as_shipped(self, request, queryset):
        """Set selected items as shipped."""
        queryset.update(product_status='shipped')
        self.message_user(request, "Selected items marked as shipped.")
    
    def mark_as_delivered(self, request, queryset):
        """Set selected items as delivered."""
        queryset.update(product_status='delivered')
        self.message_user(request, "Selected items marked as delivered.")
    
    def mark_as_cancelled(self, request, queryset):
        """Set selected items as cancelled."""
        queryset.update(product_status='cancelled')
        self.message_user(request, "Selected items marked as cancelled.")

    def mark_as_on_hold(self, request, queryset):
        """Set selected items as on hold (unavailable)."""
        queryset.update(product_status='on_hold')
        self.message_user(request, "Selected items marked as on hold.")
    
    # Add more actions as needed for other statuses
    mark_as_processing.short_description = "Mark selected items as Processing"
    mark_as_shipped.short_description = "Mark selected items as Shipped"
    mark_as_delivered.short_description = "Mark selected items as Delivered"
    mark_as_cancelled.short_description = "Mark selected items as Cancelled"
    mark_as_on_hold.short_description = "Mark selected items as On Hold"

    def order_image(self, obj):
        """Display the product image in the inline form."""
        if obj.image:
            # Ensure the image URL is correct
            image_url = obj.image if obj.image.startswith('/media/') else settings.MEDIA_URL + obj.image
            return mark_safe(f'<img src="{image_url}" width="100" height="100" />')
        return "No Image Available"

    order_image.short_description = "Image Preview"


from django.contrib import admin
from .models import CartOrder, CartOrderItems, PaymentMethod
from django.utils.safestring import mark_safe

class CartOrderItemsInline(admin.TabularInline):
    model = CartOrderItems
    extra = 1  # Number of empty rows to display by default
    fields = ['product_status', 'order_image', 'item', 'qty', 'price', 'total']  # Fields to display in the inline
    readonly_fields = ['order_image', 'total']  # Make 'total' and 'order_image' read-only
    can_delete = True  # Allow deleting items
    show_change_link = True  # Allow changing the item in the inline form

    def order_image(self, obj):
        """Display the product image in the inline form."""
        if obj.image:
            image_url = obj.image if obj.image.startswith('/media/') else settings.MEDIA_URL + obj.image
            return mark_safe(f'<img src="{image_url}" width="50" height="50" />')
        return "No Image Available"

    order_image.short_description = "Image Preview"

# Register CartOrder with CartOrderItemsInline
@admin.register(CartOrder)
class CartOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number',
        'user', 
        'guest_id', 
        'price', 
        'paid_status', 
        'order_date', 
        'product_status', 
        'delivery_method', 
        'shipping_fee', 
        'updated_by', 
    ]
    
    search_fields = ['user__username', 'guest_id', 'product_status']
    list_filter = ['paid_status', 'product_status', 'delivery_method', 'order_date']
    list_editable = ['paid_status', 'product_status', 'delivery_method']
    readonly_fields = ('user', 'guest_id',)

    inlines = [CartOrderItemsInline]  # Include CartOrderItemsInline for order items

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'payment_method')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Cart Orders Administration'
        return super().changelist_view(request, extra_context=extra_context)



@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'review', 'rating']

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'product']


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('order', 'name', 'phone', 'city', 'area', 'email', 'user', 'guest_id')  # Columns to display
    list_filter = ('city', 'area', 'user')  # Filters in the sidebar
    search_fields = ('name', 'phone', 'email', 'user__username', 'guest_id')  # Searchable fields
    ordering = ('-id',)  # Default ordering (latest entries first)
    readonly_fields = ('name', 'user', 'order', 'phone', 'city', 'area', 'address', 'email', 'order_note', 'guest_id')  # Mark fields readonly

    def has_add_permission(self, request):
        # Disable the add option in admin
        return False

    def has_delete_permission(self, request, obj=None):
        # Disable the delete option in admin
        return False


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ['name', 'charge']


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_enabled', 'description')
    list_editable = ('is_enabled',)
    search_fields = ('name',)

