from django.db import models
from business.models import Business
from django.utils.translation import gettext_lazy as _
from shortuuid.django_fields import ShortUUIDField
from django.db.models.signals import pre_save
from django.dispatch import receiver
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()  # Use custom User model if applicable

class Contact(models.Model):
    class ContactType(models.TextChoices):
        CUSTOMER = 'customer', _("Customer")
        VENDOR = 'vendor', _("Vendor")
        SUPPLIER = 'supplier', _("Supplier")
        MANUFACTURER = 'manufacturer', _("Manufacturer")
        OTHER = 'other', _("Other")

    cid = ShortUUIDField(
        unique=True, 
        length=10, 
        max_length=30, 
        prefix='con', 
        alphabet="abcdefgh12345", 
        editable=False
    )
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name=_("Business"),
    )
    type = models.CharField(
        max_length=20,
        choices=ContactType.choices,
        default=ContactType.CUSTOMER,
        verbose_name=_("Contact Type")
    )
    supplier_business_name = models.CharField(
        max_length=255, 
        blank=True, 
        null=True, 
        verbose_name=_("Supplier Business Name"),
        help_text='Only for supplier business names'
    )
    prefix = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name=_("Prefix"),
        help_text=_("e.g., Mr., Ms., Dr.")
    )
    first_name = models.CharField(max_length=100, verbose_name=_("First Name"))
    middle_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Middle Name"))
    last_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Last Name"))
    email = models.EmailField(max_length=255, blank=True, null=True, verbose_name=_("Email"))
    contact_id = models.CharField(max_length=100, blank=True, null=True, unique=True, verbose_name=_("Contact ID"))
    is_active = models.BooleanField(default=True, verbose_name="Is Active?")
    tax_number = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Tax Number"))
    
    # Address Information
    address_line1 = models.TextField(blank=True, null=True, verbose_name=_("Address Line 1"))
    address_line2 = models.TextField(blank=True, null=True, verbose_name=_("Address Line 2"))
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("City"))
    state = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("State"))
    country = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Country"))
    zip_code = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("ZIP Code"))
    shipping_address = models.TextField(blank=True, null=True, verbose_name=_("Shipping Address"))
    
    # Contact Information
    mobile = models.CharField(max_length=20, verbose_name=_("Mobile"))
    landline = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Landline"))
    alternate_number = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("Alternate Number"))

    # Financial Information
    pay_term_number = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Payment Term Number"))
    pay_term_type = models.CharField(
        max_length=10, 
        choices=[('days', 'Days'), ('months', 'Months')], 
        blank=True, 
        null=True, 
        verbose_name=_("Payment Term Type")
    )
    credit_limit = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'), 
        verbose_name=_("Credit Limit")
    )
    balance = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'), 
        verbose_name=_("Balance")
    )

    # Reward Points
    total_rp = models.PositiveIntegerField(default=0, verbose_name=_("Total Reward Points"))
    total_rp_used = models.PositiveIntegerField(default=0, verbose_name=_("Total Reward Points Used"))
    total_rp_expired = models.PositiveIntegerField(default=0, verbose_name=_("Total Reward Points Expired"))
    
    # Additional Information
    dob = models.DateField(blank=True, null=True, verbose_name=_("Date of Birth"))
    is_default = models.BooleanField(default=False, verbose_name=_("Is Default"), 
    help_text=_("Indicates if this is the primary or default contact for the business."))
    is_walk_in = models.BooleanField(default=False, help_text=_("Indicates if this is the walk-in-customer for the sales."))  # Flag for Walk-in Customer
    is_export = models.BooleanField(default=False, verbose_name=_("Is Export Contact"), help_text=_("Marks whether this contact is associated with export transactions or operations."))
    position = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Position"))
    customer_group_id = models.PositiveIntegerField(blank=True, null=True, verbose_name=_("Customer Group ID"))

    # Custom Fields
    custom_field1 = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Custom Field 1"))
    custom_field2 = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Custom Field 2"))
    custom_field3 = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Custom Field 3"))
    custom_field4 = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Custom Field 4"))
    custom_field5 = models.CharField(max_length=255, blank=True, null=True, verbose_name=_("Custom Field 5"))

    # Suggested Additions
    notes = models.TextField(blank=True, null=True, verbose_name=_("Notes"))
    tags = models.JSONField(default=list, blank=True, null=True, verbose_name=_("Tags"))
    reference = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Reference"))
    website = models.URLField(max_length=255, blank=True, null=True, verbose_name=_("Website"))
    social_media = models.JSONField(default=dict, blank=True, null=True, verbose_name=_("Social Media Links"))
    language = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Language"))
    currency = models.CharField(max_length=10, blank=True, null=True, verbose_name=_("Preferred Currency"))
    payment_terms = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Payment Terms"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='created_contacts')
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name='updated_contacts')

    class Meta:
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cid'], name='contact_idx_cid'),
            models.Index(fields=['business'], name='contact_idx_business'),
            models.Index(fields=['type'], name='contact_idx_type'),
            models.Index(fields=['email'], name='contact_idx_email'),
            models.Index(fields=['mobile'], name='contact_idx_mobile'),
            models.Index(fields=['contact_id'], name='contact_idx_contact_id'),
            models.Index(fields=['is_active'], name='contact_idx_is_active'),
            models.Index(fields=['dob'], name='contact_idx_dob'),
            models.Index(fields=['created_at'], name='contact_idx_created_at'),
            models.Index(fields=['updated_at'], name='contact_idx_updated_at'),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"  # Display full name

    # Signal to generate contact_id before saving the Contact instance
@receiver(pre_save, sender=Contact)
def generate_contact_id(sender, instance, **kwargs):
    if not instance.contact_id:
        # Map contact types to prefixes
        type_prefix_map = {
            Contact.ContactType.CUSTOMER: 'C',
            Contact.ContactType.VENDOR: 'V',
            Contact.ContactType.SUPPLIER: 'S',
            Contact.ContactType.MANUFACTURER: 'M',
            Contact.ContactType.OTHER: 'O',
        }

        # Get the prefix based on the contact type
        prefix = type_prefix_map.get(instance.type, 'O')  # Default to 'O' for 'Other'

        # Find the last contact_id with the same prefix
        last_contact = Contact.objects.filter(contact_id__startswith=prefix).order_by('-contact_id').first()
        if last_contact and last_contact.contact_id:
            last_number = int(last_contact.contact_id.split('-')[-1])  # Extract the numeric part
        else:
            last_number = 0

        # Generate the new contact_id
        instance.contact_id = f"{prefix}-{last_number + 1:05d}"

    def __str__(self):
        return f"{self.contact_id} - {self.first_name} {self.last_name}"