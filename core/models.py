from django.db import models
from django.conf import settings
from django.urls import reverse
from shortuuid.django_fields import ShortUUIDField
from django.utils.translation import gettext_lazy as _
import os
import random
from django.utils.html import mark_safe
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from taggit.managers import TaggableManager
from tinymce import models as tinymce_models
from decimal import Decimal
from uuid import uuid4

User = get_user_model()  # Use custom User model if applicable

STATUS_CHOICE = (
    ("in_review", "In Review"),
    ("processing", "Processing"),
    ("shipped", "Shipped"),
    ("delivered", "Delivered"),
    ("cancelled", "Cancelled"),
    ("refunded", "Refunded"),
    ("failed", "Payment Failed"),
    ("on_hold", "On Hold"),
    ("returned", "Returned"),
)


STATUS = (
    ("draft", "Draft"),
    ("disabled", "Disabled"),
    ("rejected", "Rejected"),
    ("in_review", "In Review"),
    ("published", "Published"),
)


RATING = (
    (1, "★☆☆☆☆"),
    (2, "★★☆☆☆"),
    (3, "★★★☆☆"),
    (4, "★★★★☆"),
    (5, "★★★★★"),
)

# This ecommerce site will manage different businesses
BUSINESS_TYPE_CHOICES = (
    ('beauty', 'Beauty'),
    ('food', 'Food & Beverage'),
)


class Category(models.Model):
    cid = ShortUUIDField(unique=True, length=10, max_length=30, prefix='cat', alphabet="abcdefgh12345", editable=False)
    title = models.CharField(max_length=100, unique=True)
    business_type = models.CharField(
        max_length=10, 
        choices=BUSINESS_TYPE_CHOICES, 
        default='food'
    )
    slug = models.SlugField(max_length=100, unique=True, blank=True, help_text='This will generate automatically')
    image = models.ImageField(upload_to='category', default='default.jpg', blank=True, null=True)
    icon = models.ImageField(upload_to='category', default='default.jpg', verbose_name=_("Navigation Menu Icon"), blank=True, null=True, help_text='Select icon for navigation menu in homepage')
    parent = models.ForeignKey(
        'self', 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        related_name='subcategories'
    )  # Self-referential for subcategories
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def category_image(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')
        return "No Image Available"
    
    def category_icon(self):
        if self.icon:
            return mark_safe(f'<img src="{self.icon.url}" width="50" height="50" />')
        return "No Icon Available"

    def __str__(self):
        return f"{self.title} ({self.parent.title})" if self.parent else self.title
        

    @property
    def has_subcategories(self):
        """Check if the category has subcategories."""
        return self.subcategories.exists()

    

class Tags(models.Model):
    pass

class Brand(models.Model):
    # Fields for brands
    cid = ShortUUIDField(unique=True, length=10, max_length=30, prefix='brn', alphabet="abcdefgh12345", editable=False)
    business_type = models.CharField(
        max_length=10, 
        choices=BUSINESS_TYPE_CHOICES, 
        default='food'
    )
    title = models.CharField(max_length=100, unique=True)
    image = models.ImageField(upload_to='brand', default='default.jpg', blank=True, null=True)
    description = tinymce_models.HTMLField(null=True, blank=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Brands'

    def brand_image(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')
        return "No Image Available"

    def __str__(self):
        return self.title


class Unit(models.Model):
    title = models.CharField(max_length=100, unique=True, help_text='Example: Piece')
    short_title = models.CharField(max_length=100, unique=True, help_text='Example: Pc(s)')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Units'

    def __str__(self):
        return self.title


def user_directory_path(instance, filename):
    return f'vendor_images/{instance.user.id}/{filename}'


# For Product Model
def product_directory_path(instance, filename):
    # Extract the file extension
    ext = filename.split('.')[-1]
    
    # Generate a slug-based filename from the product's title
    slug = slugify(instance.slug or instance.title)
    base_filename = f"{slug}.{ext}"
    
    # Check for existing files and append a number if necessary
    counter = 1
    new_filename = base_filename
    while os.path.exists(os.path.join('uploads/products/', new_filename)):
        new_filename = f"{slug}-{counter}.{ext}"
        counter += 1

    return os.path.join('products/', new_filename)

# For ProductImage Model
def product_image_directory_path(instance, filename):
    # Extract the file extension
    ext = filename.split('.')[-1]

    # Safely access the related product's slug
    if instance.product and instance.product.slug:
        slug = slugify(instance.product.slug)
    else:
        slug = "default"  # Fallback slug if product or slug is missing
    
    base_filename = f"{slug}.{ext}"
    
    # Check for existing files and append a number if necessary
    counter = 1
    new_filename = base_filename
    while os.path.exists(os.path.join('uploads/products/', new_filename)):
        new_filename = f"{slug}-{counter}.{ext}"
        counter += 1

    return os.path.join('products/', new_filename)


class Vendor(models.Model):
    vid = ShortUUIDField(unique=True, length=10, max_length=20, prefix="ven", alphabet="abcdefgh12345", editable=False)
    business_type = models.CharField(
        max_length=10, 
        choices=BUSINESS_TYPE_CHOICES, 
        default='food'
    )
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to=user_directory_path, default='default.jpg', blank=True, null=True)
    description = models.TextField(null=True, blank=True)

    address = models.CharField(max_length=100, default="123 Main Street", blank=True)
    contact = models.CharField(max_length=100, default="+123 (456) 789", blank=True)
    chat_resp_time = models.PositiveIntegerField(default=100)
    shipping_on_time = models.PositiveIntegerField(default=100)
    authentic_rating = models.PositiveIntegerField(default=100)
    days_return = models.PositiveIntegerField(default=100)
    warranty_period = models.PositiveIntegerField(default=100)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, help_text="This field is automatically set to the logged-in user.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Vendors"
    
    def vendor_image(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')
        return "No Image Available"  

    def __str__(self):
        return self.title


class Product(models.Model):
    pid = ShortUUIDField(unique=True, length=10, max_length=20, alphabet="abcdefgh12345", editable=False)
    
    title = models.CharField(max_length=100)
    title_bn = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Title (Bengali)"), help_text="Use Unicode characters for bengali")
    slug = models.SlugField(max_length=100, unique=True, blank=True, help_text="Slug will be generated automatically")
    
    image = models.ImageField(upload_to=product_directory_path, default='default.jpg')

    page_description = models.TextField(max_length=200, blank=True, null=True, help_text="Website Page Description for seo purposes, maximum 150 characters")
    description = tinymce_models.HTMLField(null=True, blank=True)
    
    business_type = models.CharField(
        max_length=10, 
        choices=BUSINESS_TYPE_CHOICES, 
        default='food'
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)

    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, help_text='Unit must be in Peice, product title contains unit name')

    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name=_("MRP"))  # Maximum 10 digits, with 2 after the decimal
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, editable=False)  # Optional old price
    
    specifications = models.TextField(null=True, blank=True)
    
    tags = TaggableManager(blank=True)

    type = models.CharField(max_length=100, null=True, blank=True)
    stock_count = models.CharField(max_length=100, default="10", null=True, blank=True)
    life = models.CharField(max_length=100, default="100 Days", null=True, blank=True)
    mfd = models.DateTimeField(auto_now_add=False, blank=True, null=True)

    product_status = models.CharField(choices=STATUS, max_length=10, default="published")

    status = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    featured = models.BooleanField(default=False)
    digital = models.BooleanField(default=False)
    best_selling = models.BooleanField(default=False)
    free_delivery = models.BooleanField(default=False)

    sold_count = models.CharField(max_length=100, null=True, blank=True, help_text="This field is automatically set.")
    review_star = models.CharField(max_length=100, null=True, blank=True, help_text="This field is automatically set. After collecting original review by customer this field will be ignored.")
    review_count = models.CharField(max_length=100, null=True, blank=True, help_text="This field is automatically set. After collecting original review by customer this field will be ignored.")

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, editable=False, help_text="This field is automatically set to the logged-in user.")
    sku = ShortUUIDField(unique=True, length=4, max_length=20, prefix="sku", alphabet="abcdefgh12345", help_text="This field is automatically set.")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Products"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Generate a random sold_count if it's not already assigned
        if not self.sold_count:
            self.sold_count = str(random.randint(200, 500))

        # Automatically set random values if not provided
        if not self.review_star:
            self.review_star = str(random.choice([4, 4.5, 5]))
        if not self.review_count:
            self.review_count = str(random.randint(50, 100))

        super().save(*args, **kwargs)
    
    def product_image(self):
        if self.image:
            return mark_safe(f'<img src="{self.image.url}" width="50" height="50" />')
        return "No Image Available"

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('core:product-detail', kwargs={'slug': self.slug})

    
    def get_percentage(self):
        if self.old_price > 0:  # Ensure there's no division by zero
            discount_percentage = ((self.old_price - self.price) / self.old_price) * 100
            return discount_percentage
        return 0  # Return 0 if old_price is zero or invalid


class ProductImage(models.Model):
    image = models.ImageField(upload_to=product_image_directory_path, default='default.jpg')
    product = models.ForeignKey(Product, related_name='p_images', on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product Images"


################## Cart, Order, OrderItems ###############

class PaymentMethod(models.Model):
    PAYMENT_TYPES = [
        ('cod', 'Cash on Delivery'),
        ('bkash', 'bKash'),
        ('card', 'Pay with Card/Mobile Wallet'),
    ]
    name = models.CharField(max_length=50, choices=PAYMENT_TYPES, unique=True)
    is_enabled = models.BooleanField(default=True)  # Enable or disable the payment method
    description = models.TextField(blank=True, null=True)  # Optional description for the payment method

    def __str__(self):
        return dict(self.PAYMENT_TYPES).get(self.name, self.name)

    def get_display_name(self):
        return self.get_name_display()




from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.conf import settings
from django.utils.timezone import now
from uuid import uuid4
from decimal import Decimal


# Helper Functions
def generate_order_number():
    return f"ORD-{uuid4().hex[:8].upper()}"


class CartOrder(models.Model):
    # User Information
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='customer_orders')
    guest_id = models.CharField(max_length=255, null=True, blank=True)  # For guest orders

    # Order Details
    order_number = models.CharField(max_length=20, unique=True, default=generate_order_number)
    items_count = models.PositiveIntegerField(default=0, editable=False)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, editable=False)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    shipping_fee = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    tax_amount = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    discount = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)

    # Status and Dates
    paid_status = models.BooleanField(default=False)
    product_status = models.CharField(choices=STATUS_CHOICE, max_length=15, default="in_review")
    order_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)

    # Delivery Information
    delivery_method = models.CharField(
        max_length=100,
        choices=[('inside_dhaka', 'Inside Dhaka'), ('outside_dhaka', 'Outside Dhaka')],
        default='inside_dhaka'
    )

    # Payment Information
    payment_method = models.ForeignKey('PaymentMethod', on_delete=models.SET_NULL, null=True)
    transaction_id = models.CharField(max_length=255, null=True, blank=True)

    # Metadata
    customer_notes = models.TextField(null=True, blank=True)
    admin_notes = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    # Tracking who updated the record
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, help_text="This field is automatically set to the logged-in user.")
    

    class Meta:
        verbose_name_plural = "Cart Orders"
        ordering = ['-order_date']

    def __str__(self):
        return f"Order #{self.order_number} - {self.user or 'Guest'}"
    
    # Method to calculate the total price including shipping, tax, and discount
    def calculate_total_price(self):
        """Calculate the total price, including shipping, tax, and discounts."""
        price = Decimal(self.price) if isinstance(self.price, float) else self.price
        shipping_fee = Decimal(self.shipping_fee) if isinstance(self.shipping_fee, float) else self.shipping_fee
        tax_amount = Decimal(self.tax_amount) if isinstance(self.tax_amount, float) else self.tax_amount
        discount = Decimal(self.discount) if isinstance(self.discount, float) else self.discount

        return price + shipping_fee + tax_amount - discount
    

    def save(self, *args, **kwargs):
        """Override save method to calculate total price."""
        self.total_price = self.calculate_total_price()
        super().save(*args, **kwargs)


class CartOrderItems(models.Model):
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE)
    invoice_no = models.CharField(max_length=200, unique=True, default=generate_order_number)
    product_status = models.CharField(choices=STATUS_CHOICE, max_length=15, default="in_review")
    item = models.CharField(max_length=200)
    image = models.CharField(max_length=200)
    qty = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        verbose_name_plural = "Cart Order Items"

    def order_image(self):
        """Return image preview for the admin panel."""
        if self.image:
            # Ensure the image path is correctly prefixed with MEDIA_URL for display
            image_url = self.image if self.image.startswith('/media/') else settings.MEDIA_URL + self.image
            return mark_safe(f'<img src="{image_url}" width="50" height="50" />')
        return "No Image Available"

    def save(self, *args, **kwargs):
        """Override save to calculate total."""
        self.total = Decimal(self.price) * self.qty
        super().save(*args, **kwargs)


################## Product Review, Wishlist and Address ###############

class ProductReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, related_name="reviews")
    review = models.TextField()
    rating = models.IntegerField(choices=RATING, default=None)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Product Reviews"

    def __str__(self):
        return self.product.title

    def get_rating(self):
        return self.rating



class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Wishlists"

    def __str__(self):
        return self.product.title


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=100, null=True)
    status = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "Addresses"


import uuid

class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    guest_id = models.CharField(max_length=255, null=True, blank=True)
    order = models.OneToOneField('CartOrder', on_delete=models.CASCADE)
    name = models.CharField(max_length=255, verbose_name=_("Customer Name"), null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    city = models.CharField(max_length=255, null=True, blank=True)
    area = models.CharField(max_length=255, null=True, blank=True)
    address = models.TextField()
    email = models.EmailField(null=True, blank=True)
    order_note = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.city}"


# Shipping Methods will be implemented later
class ShippingMethod(models.Model):
    name = models.CharField(max_length=100)  # e.g., 'Inside Dhaka' or 'Outside Dhaka'
    charge = models.DecimalField(max_digits=10, decimal_places=2)  # Shipping charge for that method

    def __str__(self):
        return f"{self.name} - ৳{self.charge}"




