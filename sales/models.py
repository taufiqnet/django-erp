from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.timezone import now
from django.core.exceptions import ValidationError
from business.models import Business
from contact.models import Contact
from products.models import Product
from decimal import Decimal

from django.db import models
from django.utils.timezone import now
from decimal import Decimal

class Order(models.Model):
    ORDER_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Refunded', 'Refunded'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('Cash', 'Cash'),
        ('Credit Card', 'Credit Card'),
        ('Bank Transfer', 'Bank Transfer'),
        ('Digital Wallet', 'Digital Wallet'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Partially Paid', 'Partially Paid'),
        ('Refunded', 'Refunded'),
    ]

    business = models.ForeignKey(
        Business,  # Use the actual model class
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name="Business",
    )
    order_number = models.CharField(max_length=20, unique=True, editable=False)
    invoice_number = models.CharField(max_length=20, blank=True, null=True, editable=False)
    customer = models.ForeignKey(
        Contact,  # Use the actual model class
        on_delete=models.CASCADE,
    )
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # New field
    due_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # New field
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='Pending')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='Pending')
    notes = models.TextField(blank=True, null=True)
    shipping_address = models.TextField(blank=True, null=True)    
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['order_number'], name='idx_order_number'),
            models.Index(fields=['customer'], name='idx_order_customer'),
            models.Index(fields=['business'], name='idx_order_business'),
            models.Index(fields=['order_date'], name='idx_order_date'),
            models.Index(fields=['status'], name='idx_order_status'),
        ]

    def save(self, *args, **kwargs):
        # Generate order number and invoice number if not provided
        if not self.order_number:
            self.order_number = self.generate_order_number()

        if not self.invoice_number:
            self.invoice_number = self.generate_invoice_number()

        # Recalculate total amount if the order already exists
        if self.pk:
            self.recalculate_total_amount()

        # Calculate due amount and update payment status
        self.calculate_due_amount()
        self.update_payment_status()

        super().save(*args, **kwargs)

    def generate_order_number(self):
        current_year_month = now().strftime("%Y%m")
        last_order = Order.objects.filter(order_number__startswith=f"ORD-{current_year_month}").order_by('-id').first()
        new_number = int(last_order.order_number.split("-")[-1]) + 1 if last_order else 1
        return f"ORD-{current_year_month}-{new_number:04d}"
    
    def generate_invoice_number(self):
        current_year_month = now().strftime("%Y%m")
        last_invoice = Order.objects.filter(invoice_number__startswith=f"INV-{current_year_month}").order_by('-id').first()
        new_number = int(last_invoice.invoice_number.split("-")[-1]) + 1 if last_invoice else 1
        return f"INV-{current_year_month}-{new_number:04d}"

    def recalculate_total_amount(self):
        """Recalculate the total amount and update the order."""
        subtotal = sum(Decimal(item.total_price) for item in self.items.all())  # Ensure total_price is Decimal
        
        # Calculate total amount without explicitly storing tax separately
        total_amount = (subtotal + Decimal(self.shipping_cost)) - Decimal(self.discount)

        self.total_amount = total_amount

    def calculate_due_amount(self):
        """Calculate the due amount based on the total amount and paid amount."""
        self.due_amount = Decimal(self.total_amount) - Decimal(self.paid_amount)

    def update_payment_status(self):
        """Update the payment status based on the total amount and paid amount."""
        if self.paid_amount >= self.total_amount:
            self.payment_status = 'Paid'
        elif self.paid_amount > 0:
            self.payment_status = 'Partially Paid'
        else:
            self.payment_status = 'Pending'

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
    )
    product = models.ForeignKey(
        Product,  # Use the actual model class
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    item_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)

    class Meta:
        indexes = [
            models.Index(fields=['order'], name='idx_orderitem_order'),
            models.Index(fields=['product'], name='idx_orderitem_product'),
        ]

    def clean(self):
        if self.quantity > self.product.stock_quantity:
            raise ValidationError(f"Insufficient stock for {self.product.name}. Available: {self.product.stock_quantity}")

    def save(self, *args, **kwargs):
        # Ensure unit_price is set to the product's price if not provided
        if not self.unit_price:
            self.unit_price = self.product.price

        # Convert all values to Decimal for accurate calculations
        quantity = Decimal(self.quantity)
        unit_price = Decimal(self.unit_price)
        item_discount = Decimal(self.item_discount)

        # Calculate total_price
        self.total_price = quantity * (unit_price - item_discount)

        # Save the instance
        super().save(*args, **kwargs)

        # Update the order's total amount
        self.order.recalculate_total_amount()

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Order {self.order.order_number}"
    

class Payment(models.Model):
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
    ]

    order = models.ForeignKey('Order', on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Payment of {self.amount} on {self.payment_date}"
        