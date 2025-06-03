from django.contrib import admin
from .models import (
    Category, Product, Batch, Inventory,
    Prescription, PrescriptionItem, Customer,
    Sale, SaleItem, Payment, Return, ReturnItem,
    Supplier, PurchaseOrder, PurchaseOrderItem,
    StockAdjustment, StockAdjustmentItem
)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'is_active', 'sort_order')
    list_filter = ('is_active', 'business')
    search_fields = ('name', 'description')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'category', 'drug_schedule', 'requires_prescription')
    list_filter = ('drug_schedule', 'requires_prescription', 'is_active')
    search_fields = ('name', 'generic_name', 'ndc')

@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('product', 'batch_number', 'expiry_date', 'quantity')
    list_filter = ('product', 'expiry_date')
    search_fields = ('batch_number',)

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'batch', 'quantity', 'location')
    list_filter = ('location',)

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('prescription_number', 'patient', 'prescriber', 'status', 'date_prescribed')
    list_filter = ('status', 'date_prescribed')
    search_fields = ('prescription_number', 'patient__name')

@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ('prescription', 'product', 'quantity', 'filled_quantity')
    search_fields = ('prescription__prescription_number', 'product__name')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('contact', 'health_card_number', 'insurance_provider')
    search_fields = ('contact__name', 'health_card_number')

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('sale_number', 'date', 'customer', 'status', 'total')
    list_filter = ('status', 'date')
    search_fields = ('sale_number', 'customer__contact__name')

@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'product', 'quantity', 'unit_price', 'total')
    search_fields = ('sale__sale_number', 'product__name')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('sale', 'amount', 'method', 'status', 'created_at')
    list_filter = ('method', 'status')
    search_fields = ('sale__sale_number', 'transaction_id')

@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('return_number', 'sale', 'status', 'refund_amount')
    list_filter = ('status',)
    search_fields = ('return_number', 'sale__sale_number')

@admin.register(ReturnItem)
class ReturnItemAdmin(admin.ModelAdmin):
    list_display = ('return_request', 'sale_item', 'quantity', 'restocked')
    search_fields = ('return_request__return_number',)

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'business','license_number', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('company_name', 'license_number')

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('po_number', 'supplier', 'status', 'order_date', 'total')
    list_filter = ('status', 'supplier')
    search_fields = ('po_number', 'supplier__company_name')

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ('purchase_order', 'product', 'quantity', 'unit_cost')
    search_fields = ('purchase_order__po_number', 'product__name')

@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = ('adjustment_number', 'date', 'type', 'reason')
    list_filter = ('type', 'reason')
    search_fields = ('adjustment_number',)

@admin.register(StockAdjustmentItem)
class StockAdjustmentItemAdmin(admin.ModelAdmin):
    list_display = ('adjustment', 'product', 'quantity')
    search_fields = ('adjustment__adjustment_number', 'product__name')