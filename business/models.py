from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.core.validators import MinLengthValidator
from django.utils import timezone
from django.conf import settings

class Business(models.Model):
    # Unique Identifier
    bid = ShortUUIDField(unique=True, length=10, max_length=30, prefix='bus', alphabet="abcdefgh12345")
    name = models.CharField(max_length=255, verbose_name="Business Name")
    legal_name = models.CharField(max_length=255, verbose_name="Legal Name", blank=True, null=True)
    type = models.CharField(max_length=100, verbose_name="Business Type", blank=True, null=True)
    
    # Registration and Tax Information
    registration_number = models.CharField(max_length=50, verbose_name="Registration Number", blank=True, null=True, unique=True)
    tax_id = models.CharField(max_length=50, verbose_name="Tax ID", blank=True, null=True, unique=True)
    vat_number = models.CharField(max_length=50, verbose_name="VAT Number", blank=True, null=True, unique=True)

    # Contact Information
    contact_number = models.CharField(max_length=15, verbose_name="Primary Contact Number", blank=True, null=True, validators=[MinLengthValidator(7)])
    alternate_contact = models.CharField(max_length=15, verbose_name="Alternate Contact", blank=True, null=True, validators=[MinLengthValidator(7)])
    hotline = models.CharField(max_length=15, verbose_name="Hotline", blank=True, null=True, validators=[MinLengthValidator(7)])
    email = models.EmailField(verbose_name="Business Email Address", unique=True)
    support_email = models.EmailField(verbose_name="Support Email", blank=True, null=True)
    business_logo = models.ImageField(upload_to='business/', null=True, blank=True, verbose_name="Business Logo")
    
    # Address Information
    address_line1 = models.CharField(max_length=255, verbose_name="Address Line 1", blank=True, null=True)
    address_line2 = models.CharField(max_length=255, verbose_name="Address Line 2", blank=True, null=True)
    billing_address = models.CharField(max_length=255, verbose_name="Billing Address", blank=True, null=True)
    shipping_address = models.CharField(max_length=255, verbose_name="Shipping Address", blank=True, null=True)
    
    # Geographical Information
    state = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    division = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name="Country")

    # Social Media Links
    website = models.URLField(max_length=200, verbose_name="Website", blank=True, null=True)
    facebook = models.URLField(max_length=200, blank=True, null=True)
    linkedin = models.URLField(max_length=200, blank=True, null=True)
    twitter = models.URLField(max_length=200, blank=True, null=True)
    youtube = models.URLField(max_length=200, blank=True, null=True)
    instagram = models.URLField(max_length=200, blank=True, null=True)

    # Financial and Operational Details
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar'),
        ('EUR', 'Euro'),
        ('GBP', 'British Pound'),
        # Add more currencies as needed
    ]
    currency = models.CharField(max_length=10, verbose_name="Default Currency", default="USD", choices=CURRENCY_CHOICES)
    fiscal_year_start = models.DateField(verbose_name="Fiscal Year Start", blank=True, null=True)
    fiscal_year_end = models.DateField(verbose_name="Fiscal Year End", blank=True, null=True)
    timezone = models.CharField(max_length=100, verbose_name="Timezone", default="UTC")

    # Other Information
    description = models.TextField(blank=True, null=True, verbose_name="Business Description")
    industry = models.CharField(max_length=255, blank=True, null=True, verbose_name="Industry")
    employees_count = models.PositiveIntegerField(blank=True, null=True, verbose_name="Number of Employees")
    
    # Audit Fields
    is_active = models.BooleanField(default=True, verbose_name="Is Active?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    # created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='created_businesses')
    # updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='updated_businesses')
    deleted_at = models.DateTimeField(blank=True, null=True, verbose_name="Deleted At")

    class Meta:
        verbose_name = "Business"
        verbose_name_plural = "Businesses"
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['email']),
            models.Index(fields=['registration_number']),
        ]

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        self.deleted_at = timezone.now()
        self.is_active = False
        self.save()