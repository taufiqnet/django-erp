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

# Pharmacy-specific choices
DRUG_SCHEDULE_CHOICES = [
    ('OTC', 'Over The Counter'),
    ('I', 'Schedule I'),
    ('II', 'Schedule II'),
    ('III', 'Schedule III'),
    ('IV', 'Schedule IV'),
    ('V', 'Schedule V'),
]

DRUG_FORM_CHOICES = [
    ('TAB', 'Tablet'),
    ('CAP', 'Capsule'),
    ('SYR', 'Syrup'),
    ('INJ', 'Injection'),
    ('CRE', 'Cream'),
    ('OIN', 'Ointment'),
    ('SUS', 'Suspension'),
    ('DRO', 'Drops'),
    ('SUP', 'Suppository'),
    ('POW', 'Powder'),
    ('GEL', 'Gel'),
    ('AER', 'Aerosol'),
    ('LOT', 'Lotion'),
    ('SOL', 'Solution'),
    ('GAS', 'Gas'),
    ('PAS', 'Paste'),
    ('FIL', 'Film'),
    ('IMP', 'Implant'),
    ('PATCH', 'Patch'),
    ('INH', 'Inhaler'),
    ('LIN', 'Liniment'),
    ('LOZ', 'Lozenges'),
    ('SPR', 'Spray'),
    ('FOA', 'Foam'),
    ('CHEW', 'Chewable Tablet'),
    ('ELIX', 'Elixir'),
    ('ENEM', 'Enema'),
]

class Category(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='pharmacy_categories')
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
    is_prescription_required = models.BooleanField(default=False, verbose_name="Prescription Required")

    class Meta:
        verbose_name = "Pharmacy Category"
        verbose_name_plural = "Pharmacy Categories"
        ordering = ['sort_order', 'name']
        unique_together = ('business', 'name')

    def __str__(self):
        return self.name


class Supplier(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='pharmacy_suppliers')
    # contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='supplier_relations')
    company_name = models.CharField(max_length=100)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    tax_id = models.CharField(max_length=50, blank=True, null=True)
    primary_contact_name = models.CharField(max_length=100, blank=True, null=True)
    primary_contact_phone = models.CharField(max_length=20, blank=True, null=True)
    primary_contact_email = models.EmailField(blank=True, null=True)
    payment_terms = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"
        unique_together = ('business', 'company_name')

    def __str__(self):
        return self.company_name


class Product(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='pharmacy_products')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    barcode = models.CharField(max_length=50, blank=True, null=True, unique=True)
    sku = models.CharField(max_length=50, blank=True, null=True)
    upc = models.CharField(max_length=50, blank=True, null=True)
    ndc = models.CharField(max_length=50, blank=True, null=True, verbose_name="National Drug Code")
    drug_schedule = models.CharField(max_length=5, choices=DRUG_SCHEDULE_CHOICES, default='OTC')
    drug_form = models.CharField(max_length=5, choices=DRUG_FORM_CHOICES, blank=True, null=True)
    strength = models.CharField(max_length=50, blank=True, null=True)
    dosage = models.CharField(max_length=100, blank=True, null=True)
    requires_prescription = models.BooleanField(default=False)
    is_controlled = models.BooleanField(default=False)
    is_taxable = models.BooleanField(default=True)
    tax_type = models.CharField(max_length=10, choices=TAX_TYPE_CHOICES, default='standard')
    is_active = models.BooleanField(default=True)
    is_inventory_tracked = models.BooleanField(default=True)
    reorder_level = models.PositiveIntegerField(default=10)
    image = models.ImageField(upload_to='product_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pharmacy Product"
        verbose_name_plural = "Pharmacy Products"
        ordering = ['name']
        unique_together = ('business', 'ndc')

    def __str__(self):
        return f"{self.name} ({self.strength})" if self.strength else self.name


class Batch(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=50)
    manufacturing_date = models.DateField()
    expiry_date = models.DateField()
    quantity = models.PositiveIntegerField(default=0)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    mrp = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Maximum Retail Price")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Batch"
        verbose_name_plural = "Batches"
        unique_together = ('product', 'batch_number')

    def __str__(self):
        return f"{self.product.name} - Batch: {self.batch_number} (Exp: {self.expiry_date})"


class Inventory(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='inventory', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=0)
    location = models.CharField(max_length=50, blank=True, null=True)
    last_checked = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Inventory"
        verbose_name_plural = "Inventories"
        unique_together = ('product', 'batch')

    def __str__(self):
        return f"{self.product.name} - Qty: {self.quantity}"


class Prescription(models.Model):
    PRESCRIPTION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('filled', 'Filled'),
        ('partially_filled', 'Partially Filled'),
        ('cancelled', 'Cancelled'),
    ]
    
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='prescriptions')
    prescription_number = models.CharField(max_length=20, unique=True)
    patient = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='prescriptions')
    prescriber = models.ForeignKey(Contact, on_delete=models.SET_NULL, null=True, blank=True, 
                                 related_name='prescribed_prescriptions')
    date_prescribed = models.DateField()
    date_filled = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PRESCRIPTION_STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Prescription"
        verbose_name_plural = "Prescriptions"
        ordering = ['-date_prescribed']

    def __str__(self):
        return f"Prescription #{self.prescription_number} for {self.patient}"


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    dosage = models.CharField(max_length=100, blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)
    instructions = models.TextField(blank=True, null=True)
    filled_quantity = models.PositiveIntegerField(default=0)
    is_substituted = models.BooleanField(default=False)
    substitution_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Prescription Item"
        verbose_name_plural = "Prescription Items"

    def __str__(self):
        return f"{self.product.name} - {self.quantity} for {self.prescription}"
    


from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

# Previous models (Category, Manufacturer, Product, Batch, Inventory, Prescription, PrescriptionItem) would be here

class Customer(models.Model):
    """Extended from Contact model with pharmacy-specific fields"""
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, primary_key=True, related_name='pharmacy_customer')
    health_card_number = models.CharField(max_length=50, blank=True, null=True)
    insurance_provider = models.CharField(max_length=100, blank=True, null=True)
    insurance_number = models.CharField(max_length=50, blank=True, null=True)
    allergies = models.TextField(blank=True, null=True)
    chronic_conditions = models.TextField(blank=True, null=True)
    preferred_pharmacist = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pharmacy Customer"
        verbose_name_plural = "Pharmacy Customers"

    def __str__(self):
        return str(self.contact)


class Sale(models.Model):
    SALE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('completed', 'Completed'),
        ('voided', 'Voided'),
        ('returned', 'Returned'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='pharmacy_sales')
    sale_number = models.CharField(max_length=20, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    prescription = models.ForeignKey(Prescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    date = models.DateTimeField(default=now)
    status = models.CharField(max_length=20, choices=SALE_STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='sales_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Sale"
        verbose_name_plural = "Sales"
        ordering = ['-date']

    def __str__(self):
        return f"Sale #{self.sale_number}"

    def save(self, *args, **kwargs):
        # Calculate totals before saving
        if self.pk:
            items = self.items.all()
            self.subtotal = sum(item.total for item in items)
            self.total = self.subtotal + self.tax_amount - self.discount_amount
        super().save(*args, **kwargs)


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, null=True, blank=True)
    prescription_item = models.ForeignKey(PrescriptionItem, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sale Item"
        verbose_name_plural = "Sale Items"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def save(self, *args, **kwargs):
        discount_amount = (self.unit_price * self.quantity) * (self.discount_percent / 100)
        subtotal = (self.unit_price * self.quantity) - discount_amount
        self.total = subtotal + (subtotal * (self.tax_rate / 100))
        super().save(*args, **kwargs)
        
        # Update inventory if sale is completed
        if self.sale.status == 'completed' and self.product.is_inventory_tracked:
            inventory, created = Inventory.objects.get_or_create(
                product=self.product,
                batch=self.batch,
                defaults={'quantity': 0}
            )
            inventory.quantity -= self.quantity
            inventory.save()


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Credit/Debit Card'),
        ('insurance', 'Insurance'),
        ('bank_transfer', 'Bank Transfer'),
        ('mobile_money', 'Mobile Money'),
        ('other', 'Other'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('partially_refunded', 'Partially Refunded'),
    ]

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='completed')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Payment"
        verbose_name_plural = "Payments"
        ordering = ['-created_at']

    def __str__(self):
        return f"Payment of {self.amount} for {self.sale}"


class Return(models.Model):
    RETURN_STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]

    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='returns')
    return_number = models.CharField(max_length=20, unique=True)
    date = models.DateTimeField(default=now)
    status = models.CharField(max_length=20, choices=RETURN_STATUS_CHOICES, default='requested')
    reason = models.TextField()
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Return"
        verbose_name_plural = "Returns"
        ordering = ['-date']

    def __str__(self):
        return f"Return #{self.return_number} for {self.sale}"


class ReturnItem(models.Model):
    return_request = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    sale_item = models.ForeignKey(SaleItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    reason = models.TextField(blank=True, null=True)
    restocked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Return Item"
        verbose_name_plural = "Return Items"

    def __str__(self):
        return f"{self.quantity} x {self.sale_item.product.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update inventory if restocked
        if self.restocked and self.sale_item.product.is_inventory_tracked:
            inventory, created = Inventory.objects.get_or_create(
                product=self.sale_item.product,
                batch=self.sale_item.batch,
                defaults={'quantity': 0}
            )
            inventory.quantity += self.quantity
            inventory.save()





class PurchaseOrder(models.Model):
    PO_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ordered', 'Ordered'),
        ('received', 'Received'),
        ('partially_received', 'Partially Received'),
        ('cancelled', 'Cancelled'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='purchase_orders')
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    po_number = models.CharField(max_length=20, unique=True)
    order_date = models.DateField()
    expected_delivery_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=PO_STATUS_CHOICES, default='draft')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Purchase Order"
        verbose_name_plural = "Purchase Orders"
        ordering = ['-order_date']

    def __str__(self):
        return f"PO #{self.po_number}"


class PurchaseOrderItem(models.Model):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    received_quantity = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(null=True, blank=True)
    batch_number = models.CharField(max_length=50, blank=True, null=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Purchase Order Item"
        verbose_name_plural = "Purchase Order Items"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def save(self, *args, **kwargs):
        self.total = self.quantity * self.unit_cost
        super().save(*args, **kwargs)


class StockAdjustment(models.Model):
    ADJUSTMENT_TYPE_CHOICES = [
        ('addition', 'Addition'),
        ('subtraction', 'Subtraction'),
        ('transfer', 'Transfer'),
        ('correction', 'Correction'),
    ]

    ADJUSTMENT_REASON_CHOICES = [
        ('expired', 'Expired Goods'),
        ('damaged', 'Damaged Goods'),
        ('lost', 'Lost Inventory'),
        ('theft', 'Theft'),
        ('count_error', 'Counting Error'),
        ('other', 'Other'),
    ]

    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='stock_adjustments')
    adjustment_number = models.CharField(max_length=20, unique=True)
    date = models.DateTimeField(default=now)
    type = models.CharField(max_length=20, choices=ADJUSTMENT_TYPE_CHOICES)
    reason = models.CharField(max_length=20, choices=ADJUSTMENT_REASON_CHOICES)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Stock Adjustment"
        verbose_name_plural = "Stock Adjustments"
        ordering = ['-date']

    def __str__(self):
        return f"Adjustment #{self.adjustment_number}"


class StockAdjustmentItem(models.Model):
    adjustment = models.ForeignKey(StockAdjustment, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    from_location = models.CharField(max_length=50, blank=True, null=True)
    to_location = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Stock Adjustment Item"
        verbose_name_plural = "Stock Adjustment Items"

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update inventory
        if self.adjustment.type in ['addition', 'correction']:
            inventory, created = Inventory.objects.get_or_create(
                product=self.product,
                batch=self.batch,
                defaults={'quantity': 0}
            )
            inventory.quantity += self.quantity
            inventory.save()
        elif self.adjustment.type == 'subtraction':
            inventory = Inventory.objects.get(product=self.product, batch=self.batch)
            inventory.quantity -= self.quantity
            inventory.save()