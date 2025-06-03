from django.db import models
from business.models import Business
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
from django.db import models
from django.contrib.auth.models import AbstractUser

# (Keep your existing CHOICES tuples)

class User(AbstractUser):
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    username = models.CharField(max_length=100, unique=True)
    bio = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return f"{self.username}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Business relationship (nullable for customers)
    business = models.ForeignKey(
        Business, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='staff_profiles',
        help_text="Business this user belongs to (for vendors/staff)"
    )
    
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='customer'
    )
    
    allowed_business_type = models.CharField(
        max_length=10,
        choices=BUSINESS_TYPE_CHOICES,
        blank=True,
        null=True,
        help_text="Applicable for Vendors. Defines the type of business they manage."
    )
    
    customer_tier = models.CharField(
        max_length=10,
        choices=CUSTOMER_TIER_CHOICES,
        blank=True,
        null=True,
        help_text="Applicable for Customers. Defines their subscription type."
    )

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    # Business is required for vendor/staff, optional for customers
                    models.Q(user_type__in=['vendor', 'staff'], business__isnull=False) |
                    models.Q(user_type='customer', business__isnull=True)
                ),
                name="business_required_for_vendors"
            ),
            models.CheckConstraint(
                check=models.Q(
                    # Business type must match for vendors
                    models.Q(user_type='vendor', allowed_business_type__isnull=False) |
                    models.Q(user_type__in=['customer', 'staff'])
                ),
                name="business_type_required_for_vendors"
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.user_type.capitalize()}"
