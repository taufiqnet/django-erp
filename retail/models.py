from django.db import models
from business.models import Business
from contact.models import Contact
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.utils.html import mark_safe
from decimal import Decimal
from django.db.models import Max, Sum
import uuid
from django.utils.timezone import now
from django.core.validators import MinValueValidator

TAX_TYPE_CHOICES = [
        ('exempt', 'Tax Exempt'),
        ('standard', 'Standard Rate'),
        ('reduced', 'Reduced Rate'),
        ('zero', 'Zero Rate'),
    ]

class Category(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='retail_categories')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveIntegerField(default=0)
    image = models.ImageField(upload_to='category_images/', blank=True, null=True)
    meta_title = models.CharField(max_length=100, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Category"
        verbose_name_plural = "Categories"
        ordering = ['sort_order', 'name']
        unique_together = ('business', 'name')

    def __str__(self):
        return self.name

class Unit(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='retail_units')
    name = models.CharField(max_length=50, verbose_name=_("Unit Name"))
    abbreviation = models.CharField(max_length=10, verbose_name=_("Abbreviation"))
    description = models.TextField(blank=True, null=True, verbose_name=_("Description"))
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = "Unit"
        verbose_name_plural = "Units"
        unique_together = ('business', 'name')

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"

class Product(models.Model):
    PRODUCT_TYPE_CHOICES = [
        ('simple', 'Simple Product'),
        ('variable', 'Variable Product'),
        ('composite', 'Composite Product'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='retail_products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    short_description = models.TextField(blank=True, null=True, max_length=160)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU", editable=False)
    upc = models.CharField(max_length=50, unique=True, blank=True, null=True, verbose_name="UPC/EAN")
    barcode = models.CharField(max_length=100, blank=True, null=True, editable=False)
    type = models.CharField(max_length=20, choices=PRODUCT_TYPE_CHOICES, default='simple')
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Pricing
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    original_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, validators=[MinValueValidator(0)])
    tax_type = models.CharField(max_length=20, choices=TAX_TYPE_CHOICES, default='standard')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Inventory
    stock_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    low_stock_threshold = models.PositiveIntegerField(default=10)
    manage_stock = models.BooleanField(default=True)
    stock_status = models.CharField(max_length=20, choices=[
        ('in_stock', 'In Stock'),
        ('out_of_stock', 'Out of Stock'),
        ('backorder', 'Available on Backorder'),
    ], default='in_stock')
    
    # Shipping
    weight = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    height = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    width = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    length = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    requires_shipping = models.BooleanField(default=True)
    
    # Media
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    gallery = models.JSONField(blank=True, null=True)  # For multiple images
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_bestseller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=True)
    
    # Relations
    supplier = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'type': 'supplier'})
    related_products = models.ManyToManyField('self', blank=True)
    
    # Metadata
    meta_title = models.CharField(max_length=100, blank=True, null=True)
    meta_description = models.TextField(blank=True, null=True)
    meta_keywords = models.CharField(max_length=255, blank=True, null=True)
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_products_retail')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='updated_products_retail')

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['upc']),
            models.Index(fields=['name']),
            models.Index(fields=['business', 'is_active']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.name} ({self.sku})"

    def save(self, *args, **kwargs):
        if not self.sku:
            self.sku = self.generate_sku()
        if not self.barcode:
            self.barcode = self.generate_barcode()
            
        # Update stock status based on quantity
        if self.manage_stock:
            if self.stock_quantity <= 0:
                self.stock_status = 'out_of_stock'
            elif self.stock_quantity <= self.low_stock_threshold:
                self.stock_status = 'backorder'
            else:
                self.stock_status = 'in_stock'
                
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

    @property
    def current_price(self):
        return self.sale_price if self.sale_price else self.price

    def get_tax_amount(self, price=None):
        if price is None:
            price = self.current_price
        return price * (self.tax_rate / 100)

class Sale(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('mobile', 'Mobile Payment'),
        ('bank', 'Bank Transfer'),
        ('credit', 'Customer Credit'),
        ('mixed', 'Mixed Payment'),
    ]

    PAYMENT_STATUS = [
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('unpaid', 'Unpaid'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]

    SALE_STATUS = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold'),
    ]

    # Core Fields
    invoice_number = models.CharField(max_length=20, unique=True, editable=False)
    date = models.DateTimeField(default=now)
    status = models.CharField(max_length=20, choices=SALE_STATUS, default='completed')
    
    # Relationships
    business = models.ForeignKey(Business, on_delete=models.PROTECT, related_name='sales')
    customer = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        related_name='sales',
        null=True,
        blank=True,
        verbose_name=_("Customer")
    )
    
    # Financial Breakdown
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Payment Information
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, default='cash')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='paid')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    is_due = models.BooleanField(default=False)
    due_date = models.DateField(blank=True, null=True)
    
    # Shipping Information
    shipping_address = models.JSONField(blank=True, null=True)
    shipping_method = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    
    # Notes
    customer_note = models.TextField(blank=True, null=True)
    staff_note = models.TextField(blank=True, null=True)
    
    # Audit Fields
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='created_sales'
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_sales'
    )

    class Meta:
        verbose_name = _("Sale")
        verbose_name_plural = _("Sales")
        ordering = ['-date']
        indexes = [
            models.Index(fields=['invoice_number']),
            models.Index(fields=['business', 'date']),
            models.Index(fields=['customer']),
            models.Index(fields=['payment_status']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Invoice #{self.invoice_number}"

    def generate_invoice_number(self):
        prefix = "INV"           # self.business.invoice_prefix or "INV"
        current_year_month = now().strftime("%Y%m")
        last_invoice = Sale.objects.filter(
            business=self.business,
            invoice_number__startswith=f"{prefix}-{current_year_month}"
        ).order_by('-id').first()
        
        if last_invoice:
            last_num = int(last_invoice.invoice_number.split("-")[-1])
            new_num = last_num + 1
        else:
            new_num = 1
            
        return f"{prefix}-{current_year_month}-{new_num:05d}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()
            
        # Calculate balance due
        self.balance_due = max(self.grand_total - self.amount_paid, Decimal('0.00'))
        
        # Update payment status
        if self.amount_paid >= self.grand_total:
            self.payment_status = 'paid'
            self.is_due = False
        elif self.amount_paid > 0:
            self.payment_status = 'partial'
            self.is_due = True
        else:
            self.payment_status = 'unpaid'
            self.is_due = True
            
        super().save(*args, **kwargs)

    def calculate_totals(self):
        """Calculate all financial totals with proper tax handling"""
        items = self.items.all()
        
        # Calculate subtotal
        self.subtotal = sum(item.subtotal for item in items)
        
        # Calculate discount (if percentage-based)
        if hasattr(self, 'discount_percent') and self.discount_percent > 0:
            self.discount_amount = self.subtotal * (self.discount_percent / 100)
        else:
            self.discount_amount = getattr(self, 'discount_amount', Decimal('0.00'))
        
        # Calculate tax (item-level rates)
        self.tax_amount = Decimal('0.00')
        for item in items:
            if item.tax_type != 'none':
                self.tax_amount += item.subtotal * (item.tax_rate / 100)
        
        # Calculate grand total
        self.grand_total = self.subtotal - self.discount_amount + self.tax_amount
        
        # Calculate payment status
        self.balance_due = max(self.grand_total - self.amount_paid, Decimal('0.00'))
        # self.is_paid = self.balance_due == Decimal('0.00')
        
        self.save()

class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sale_items')
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=1, validators=[MinValueValidator(0.001)])
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    returned_quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)
    notes = models.TextField(blank=True, null=True)
    tax_type = models.CharField(max_length=20, choices=TAX_TYPE_CHOICES, default='standard')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = _("Sale Item")
        verbose_name_plural = _("Sale Items")
        ordering = ['id']

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    def save(self, *args, **kwargs):
        """Calculate subtotal before saving"""
        # Calculate item price after discount
        if self.discount_percent > 0:
            self.discount_amount = (self.price * self.quantity) * (self.discount_percent / 100)
        else:
            self.discount_amount = self.discount_amount or Decimal('0.00')
            
        # Calculate subtotal (price * quantity - discount)
        self.subtotal = (self.price * self.quantity) - self.discount_amount
        
        # Set cost price if not set
        if not self.cost_price and self.product:
            self.cost_price = self.product.cost_price
            
        super().save(*args, **kwargs)
        
        # Update parent sale totals
        self.sale.calculate_totals()

    def delete(self, *args, **kwargs):
        """Update parent sale totals after deletion"""
        sale = self.sale
        super().delete(*args, **kwargs)
        sale.calculate_totals()

    @property
    def net_quantity(self):
        return self.quantity - self.returned_quantity

class Payment(models.Model):
    PAYMENT_METHODS = Sale.PAYMENT_METHODS
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    payment_date = models.DateTimeField(default=now)
    reference = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='completed')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ['-payment_date']

    def __str__(self):
        return f"Payment of {self.amount} for {self.sale.invoice_number}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update sale payment status and amounts
        self.sale.amount_paid = self.sale.payments.filter(status='completed').aggregate(Sum('amount'))['amount__sum'] or Decimal('0.00')
        self.sale.save()
