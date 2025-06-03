from django.db import models
from django.contrib.auth.models import AbstractUser

# Define business types
BUSINESS_TYPE_CHOICES = (
    ('beauty', 'Beauty'),
    ('food', 'Food & Beverage'),
    ('retail', 'Retail'),
)

# Define user roles
USER_TYPE_CHOICES = (
    ('customer', 'Customer'),
    ('vendor', 'Vendor'),
    ('admin', 'Admin'),  # Optional: if you want to manage admin roles via model
    ('staff', 'Staff'),
)

# Define customer tiers
CUSTOMER_TIER_CHOICES = (
    ('regular', 'Regular'),
    ('premium', 'Premium'),
    ('wholesale', 'Wholesale'),
)

class User(AbstractUser):
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    username = models.CharField(max_length=100, unique=True)
    bio = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return f"{self.username}"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='customer'  # Default to customer
    )
    allowed_business_type = models.CharField(
        max_length=10,
        choices=BUSINESS_TYPE_CHOICES,
        blank=True,
        null=True,  # Vendors only
        help_text="Applicable for Vendors. Defines the type of business they manage."
    )
    customer_tier = models.CharField(
        max_length=10,
        choices=CUSTOMER_TIER_CHOICES,
        blank=True,
        null=True,  # Customers only
        help_text="Applicable for Customers. Defines their subscription type."
    )

    def __str__(self):
        return f"{self.user.username} - {self.user_type.capitalize()}"
