from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):  # or admin.StackedInline for a different layout
    model = OrderItem
    extra = 1  # Number of empty forms to display for adding new OrderItems
    readonly_fields = ('total_price',)  # Make total_price read-only
    fields = ('product', 'quantity', 'unit_price', 'item_discount', 'total_price')

    def has_add_permission(self, request, obj=None):
        # Prevent adding OrderItems directly via the admin (only through Order)
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting OrderItems directly via the admin
        return False

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'invoice_number', 'customer', 'order_date', 'total_amount', 'paid_amount', 'due_amount', 'payment_status', 'status', 'shipping_cost', 'tracking_number',)
    list_filter = ('status', 'payment_status', 'payment_method', 'order_date')
    search_fields = ('order_number', 'customer__first_name', 'tracking_number')
    readonly_fields = ('order_number', 'invoice_number', 'total_amount', 'tax_amount', 'order_date')
    inlines = [OrderItemInline]  # Add OrderItemInline to manage OrderItems within Order

    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'invoice_number', 'customer', 'order_date', 'status', 'notes'),
        }),
        ('Payment Information', {
            'fields': ('total_amount', 'tax_amount', 'payment_method', 'payment_status'),
        }),
        ('Shipping Information', {
            'fields': ('shipping_address', 'shipping_cost', 'tracking_number'),
        }),
    )

    def save_model(self, request, obj, form, change):
        # Automatically set the total_amount when saving the order
        obj.total_amount = obj.calculate_total_amount()
        super().save_model(request, obj, form, change)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'product',
        'quantity',
        'unit_price',
        'item_discount',
        'total_price',
    )
    list_filter = ('order__status', 'product__category')
    search_fields = ('order__order_number', 'product__name')
    readonly_fields = ('total_price',)

    def has_add_permission(self, request):
        # Prevent adding OrderItems directly via the admin (only through Order)
        return False

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting OrderItems directly via the admin
        return False