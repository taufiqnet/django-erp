from django.db import models
from shortuuid.django_fields import ShortUUIDField

class Company(models.Model):
    cid = ShortUUIDField(unique=True, length=10, max_length=30, prefix='com', alphabet="abcdefgh12345")
    name = models.CharField(max_length=255, verbose_name="Company Name")
    type = models.CharField(max_length=255, verbose_name="Company Type", blank=True, null=True)

    # contact information
    contact_number = models.CharField(max_length=15, verbose_name="Contact Number", blank=True, null=True)
    hotline = models.CharField(max_length=15, verbose_name="Hotline", blank=True, null=True)
    email = models.EmailField(verbose_name="Email Address", unique=True, blank=False, null=False)
    company_logo = models.ImageField(upload_to='company/', null=True, blank=True, verbose_name="Company Logo")

    # address information
    address_one = models.CharField(max_length=255, verbose_name="Company Address 1", blank=True, null=True)
    address_two = models.CharField(max_length=255, verbose_name="Company Address 2", blank=True, null=True)
    address_invoice = models.CharField(max_length=255, verbose_name="Company Address for Invoice", blank=True, null=True, help_text="Address field for Invoice Print Copy")

    # address more information
    state = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    division = models.CharField(max_length=255, blank=True, null=True)
    Country = models.CharField(max_length=255, blank=True, null=True)
    
    #social account
    website = models.CharField(max_length=200, verbose_name="Website", blank=True, null=True)
    facebook = models.CharField(max_length=200, blank=True, null=True)
    linkedIn = models.CharField(max_length=200, blank=True, null=True)
    youtube = models.CharField(max_length=200, blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company"
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name

