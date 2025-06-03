from django.db import models
from business.models import Business
from contact.models import Contact
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe
from decimal import Decimal
from django.db.models import Max
import uuid

class Category(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name
    
    
class Unit(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='units')
    name = models.CharField(max_length=50, unique=True, verbose_name=_("Unit Name"))
    abbreviation = models.CharField(max_length=10, unique=True, verbose_name=_("Abbreviation"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))

    class Meta:
        verbose_name = "Unit"
        verbose_name_plural = "Units"

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class Product(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='products')
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
    image = models.ImageField(upload_to='products/', blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    meta_title = models.CharField(max_length=255, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    keywords = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Supplier field referencing the Contact model
    supplier = models.ForeignKey(
        Contact,  # Reference to the Contact model
        on_delete=models.SET_NULL,  # Set supplier to NULL if the contact is deleted
        null=True,
        blank=True,
        related_name='supplied_products',  # Reverse relationship for Contact
        verbose_name=_("Supplier"),
        limit_choices_to={'type': 'supplier'},  # Limit choices to contacts of type 'supplier'
        help_text=_("The supplier of this product.")
    )

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='created_products')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='updated_products')

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku'], name='product_idx_sku'),
            models.Index(fields=['upc'], name='product_idx_upc'),
            models.Index(fields=['business'], name='product_idx_business'),
            models.Index(fields=['name'], name='product_idx_name'),
            models.Index(fields=['created_at'], name='product_idx_created_at'),
            models.Index(fields=['updated_at'], name='product_idx_updated_at'),
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
    

from django.db import models
from django.utils.translation import gettext_lazy as _
from uuid import uuid4

class ProductVariation(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variations',
        verbose_name=_("Parent Product"),
        help_text=_("The parent product this variation belongs to.")
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Variation Name"),
        help_text=_("The name of the variation (e.g., 'Red', 'Large').")
    )
    sku = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_("Stock Keeping Unit"),
        editable=False
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Price"),
        help_text=_("The price of this specific variation.")
    )
    cost_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_("Cost Price"),
        help_text=_("The cost price of this specific variation.")
    )
    original_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Original Price")
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Stock Quantity"),
        help_text=_("The available stock quantity for this variation.")
    )
    low_stock_threshold = models.PositiveIntegerField(
        default=10,
        verbose_name=_("Low Stock Threshold"),
        help_text=_("The threshold at which the stock is considered low.")
    )
    is_out_of_stock = models.BooleanField(
        default=False,
        verbose_name=_("Out of Stock"),
        help_text=_("Indicates if this variation is out of stock.")
    )
    barcode = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        editable=False,
        verbose_name=_("Barcode"),
        help_text=_("The barcode for this specific variation.")
    )
    weight = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Weight"),
        help_text=_("The weight of this specific variation.")
    )
    height = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Height"),
        help_text=_("The height of this specific variation.")
    )
    width = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Width"),
        help_text=_("The width of this specific variation.")
    )
    length = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name=_("Length"),
        help_text=_("The length of this specific variation.")
    )
    image = models.ImageField(
        upload_to='product_variations/',
        blank=True,
        null=True,
        verbose_name=_("Image"),
        help_text=_("An image of this specific variation.")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Indicates if this variation is active and available for sale.")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='created_variant_products')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='updated_variant_products')


    class Meta:
        verbose_name = _("Product Variation")
        verbose_name_plural = _("Product Variations")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku'], name='variation_idx_sku'),
            models.Index(fields=['product'], name='variation_idx_product'),
            models.Index(fields=['name'], name='variation_idx_name'),
            models.Index(fields=['created_at'], name='variation_idx_created_at'),
            models.Index(fields=['updated_at'], name='variation_idx_updated_at'),
        ]

    def __str__(self):
        return f"{self.product.name} - {self.name}"

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self.generate_sku()
        if not self.barcode:
            self.barcode = self.generate_barcode()
        super().save(*args, **kwargs)

    def generate_sku(self):
        product_sku = self.product.sku
        variation_id = self.get_next_variation_id()
        return f"{product_sku}-VAR-{variation_id}"

    def get_next_variation_id(self):
        max_id = ProductVariation.objects.filter(product=self.product).aggregate(models.Max('id'))['id__max']
        return (max_id or 0) + 1

    def generate_barcode(self):
        return str(uuid4()).replace('-', '').upper()[:12]