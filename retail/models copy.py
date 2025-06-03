from django.db import models
from business.models import Business
from contact.models import Contact
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe
from decimal import Decimal
from django.db.models import Max
import uuid
from django.utils.timezone import now


class Category(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='categoriesr_retail')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
    

class Unit(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='units_retail')
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Unit Name"))
    abbreviation = models.CharField(max_length=10, unique=True, verbose_name=_("Abbreviation"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))

    class Meta:
        verbose_name = "Unit"
        verbose_name_plural = "Units"

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"
    

class Product(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='products_retail')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU", editable=False, help_text='Stock Keeping Unit')
    unit = models.ForeignKey(
        Unit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Unit of Measurement"),
        help_text=_("The unit in which the product is measured (e.g., kg, piece, liter).")
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="MRP")
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cost Price", blank=True, null=True)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    is_out_of_stock = models.BooleanField(default=False)
    barcode = models.CharField(max_length=100, blank=True, null=True, editable=False)
    upc = models.CharField(max_length=50, unique=True, blank=True, null=True)
    weight = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    length = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    image = models.ImageField(upload_to='retailproducts/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Supplier field referencing the Contact model
    supplier = models.ForeignKey(
        Contact,  # Reference to the Contact model
        on_delete=models.SET_NULL,  # Set supplier to NULL if the contact is deleted
        null=True,
        blank=True,
        related_name='supplied_products_retail',  # Reverse relationship for Contact
        verbose_name=_("Supplier"),
        limit_choices_to={'type': 'supplier'},  # Limit choices to contacts of type 'supplier'
        help_text=_("The supplier of this product.")
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='created_products_retail')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='updated_products_retail')

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku'], name='pos_product_idx_sku'),
            models.Index(fields=['upc'], name='pos_product_idx_upc'),
            models.Index(fields=['business'], name='pos_product_idx_business'),
            models.Index(fields=['name'], name='pos_product_idx_name'),
            models.Index(fields=['created_at'], name='pos_product_idx_created_at'),
            models.Index(fields=['updated_at'], name='pos_product_idx_updated_at'),
        ]
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self.generate_sku()
        if not self.barcode:
            self.barcode = self.generate_barcode()
        super().save(*args, **kwargs)

    def generate_sku(self):
        business_prefix = f"B{self.business.id}"
        category_prefix = f"C{self.category.id}" if self.category else "C0"
        product_id = self.get_next_product_id()
        return f"{business_prefix}-{category_prefix}-P{product_id}"
    
    def get_next_product_id(self):
        max_id = Product.objects.filter(business=self.business).aggregate(Max('id'))['id__max']
        return (max_id or 0) + 1

    def generate_barcode(self):
        return str(uuid.uuid4()).replace('-', '').upper()[:12]



# class Sale(models.Model):
#     invoice_number = models.CharField(max_length=20, unique=True)
#     business = models.ForeignKey(Business, on_delete=models.CASCADE)
#     total_amount = models.DecimalField(max_digits=10, decimal_places=2)
#     vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     grand_total = models.DecimalField(max_digits=10, decimal_places=2)
#     date = models.DateTimeField(auto_now_add=True)

#     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='created_sale')
#     updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='updated_sale')

#     def generate_invoice_number(self):
#         current_year_month = now().strftime("%Y%m")
#         last_invoice = Sale.objects.filter(invoice_number__startswith=f"INV-{current_year_month}").order_by('-id').first()
#         new_number = int(last_invoice.invoice_number.split("-")[-1]) + 1 if last_invoice else 1
#         return f"INV-{current_year_month}-{new_number:04d}"

#     def __str__(self):
#         return f"Invoice #{self.invoice_number}"
    

# class SaleItem(models.Model):
#     sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
#     product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
#     quantity = models.PositiveIntegerField()
#     price = models.DecimalField(max_digits=10, decimal_places=2)
#     subtotal = models.DecimalField(max_digits=10, decimal_places=2)

#     def __str__(self):
#         return f"{self.product.name} x {self.quantity}"


from django.db import models
from django.conf import settings
from django.utils.timezone import now
from decimal import Decimal

PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Payment'),
        ('bank', 'Bank Transfer'),
        ('credit', 'Customer Credit')
    ]

class Sale(models.Model):  

    # Core Fields
    invoice_number = models.CharField(max_length=20, unique=True)
    date = models.DateTimeField(auto_now_add=True)
    
    # Relationships
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    customer = models.ForeignKey(
        Contact,
        on_delete=models.CASCADE,
        related_name='sales',
        verbose_name=_("Customer"),
        help_text=_("The contact who made this purchase")
    )
    
    # Financial Breakdown
    subtotal = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        verbose_name=_("Subtotal (excl. tax)")
    )
    vat_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2, 
        default=0,
        verbose_name=_("VAT Amount")
    )
    grand_total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Total Payable")
    )
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Audit Fields
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='created_sales'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name='updated_sales'
    )

    class Meta:
        ordering = ['-date']
        verbose_name = _("Sale")
        verbose_name_plural = _("Sales")
        indexes = [
            models.Index(fields=['invoice_number'], name='sale_idx_invoice'),
            models.Index(fields=['customer'], name='sale_idx_customer'),
            models.Index(fields=['business'], name='sale_idx_business'),
            models.Index(fields=['date'], name='sale_idx_date'),
        ]

    def generate_invoice_number(self):
        current_year_month = now().strftime("%Y%m")
        last_invoice = Sale.objects.filter(
            invoice_number__startswith=f"INV-{current_year_month}"
        ).order_by('-id').first()
        new_number = int(last_invoice.invoice_number.split("-")[-1]) + 1 if last_invoice else 1
        return f"INV-{current_year_month}-{new_number:04d}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
        super().save(*args, **kwargs)
        # Don't call calculate_totals() here to prevent recursion
        # It will be called after items are added

    def calculate_totals(self):
        """Calculates and updates subtotal, VAT, and grand_total from related SaleItems"""
        self.subtotal = sum(
            item.subtotal for item in self.items.all() 
            if item.subtotal is not None
        )
        self.vat_amount = self.subtotal * Decimal('0.0')  # 0% VAT as per your model
        self.grand_total = self.subtotal + self.vat_amount
        self.save(update_fields=['subtotal', 'vat_amount', 'grand_total'])

    def __str__(self):
        return f"Invoice #{self.invoice_number}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    class Meta:
        ordering = ['id']

    def save(self, *args, **kwargs):
        """Auto-calculate subtotal (price * quantity) before saving"""
        self.subtotal = self.price * self.quantity
        super().save(*args, **kwargs)
        # Update parent sale totals
        self.sale.calculate_totals()

    def delete(self, *args, **kwargs):
        """Update parent sale totals after deletion"""
        sale = self.sale
        super().delete(*args, **kwargs)
        sale.calculate_totals()

    def __str__(self):
        return f"{self.product.name if self.product else 'Deleted Product'} x {self.quantity}"