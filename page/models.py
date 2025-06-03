from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
import os
from django.conf import settings
from django.utils.html import mark_safe
from django.core.files.storage import default_storage
from django.contrib.auth import get_user_model

User = get_user_model()  # Use custom User model if applicable

def image_directory_path(instance, filename):
    # Extract the file extension
    ext = filename.split('.')[-1]
    
    # Generate a slug-based filename from the product's title
    slug = slugify(instance.slug or instance.title or "untitled")
    base_filename = f"{slug}.{ext}"
    
    # Check for existing files and append a number if necessary
    counter = 1
    new_filename = base_filename
    while default_storage.exists(f"uploads/banners/{new_filename}"):
        new_filename = f"{slug}-{counter}.{ext}"
        counter += 1

    return f"banners/{new_filename}"

class Home(models.Model):
    pass

BUSINESSTYPE = (
    ("beauty", "Beauty & Skincare"),
    ("food", "Food & Beverage"),
    ("others", "Others"),
)

class Banner(models.Model):
    type = models.CharField(choices=BUSINESSTYPE, max_length=10, default="food")
    title = models.CharField(max_length=200, verbose_name=_("Title"), blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, help_text='This will be auto generated')
    description = models.TextField(verbose_name=_("Description"), blank=True, null=True)
    image = models.ImageField(upload_to=image_directory_path, verbose_name=_("Banner Image"))
    link = models.URLField(max_length=500, verbose_name=_("Link"), blank=True, null=True, help_text=_("Optional: URL to redirect when the banner is clicked."))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"), help_text=_("Lower numbers will display first."))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"), help_text=_("Toggle to show/hide the banner on the homepage."))
    # created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    # updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Banner")
        verbose_name_plural = _("Banners")
        ordering = ['order',]  # Order by display order first, then newest

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title if self.title else f"Banner {self.id}"



ADSTYPE = (
    ("beauty", "Beauty & Skincare"),
    ("food", "Food & Beverage"),
    ("others", "Others"),
)

class Ads(models.Model):
    type = models.CharField(choices=BUSINESSTYPE, max_length=10, default="food")
    title = models.CharField(max_length=200, verbose_name=_("Title"), blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, help_text='This will be auto generated')
    description = models.TextField(verbose_name=_("Description"), blank=True, null=True)
    image = models.ImageField(upload_to=image_directory_path,  verbose_name=_("Ads Image"))
    link = models.URLField(max_length=500, verbose_name=_("Link"), blank=True, null=True, help_text=_("Optional: URL to redirect when the banner is clicked."))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"), help_text=_("Lower numbers will display first."))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"), help_text=_("Toggle to show/hide the banner on the homepage."))
    # created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    # updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Ads")
        verbose_name_plural = _("Ads")
        ordering = ['order',]  # Order by display order first, then newest

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title if self.title else f"Ads {self.id}"


# Campaign will be shown in the header as navbar and also as image in the homepage
class Campaign(models.Model):
    type = models.CharField(choices=BUSINESSTYPE, max_length=10, default="food")
    title = models.CharField(max_length=200, verbose_name=_("Title"), blank=True, null=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True, help_text='This will be auto generated')
    slogan = models.CharField(max_length=200, verbose_name=_("slogan"), blank=True, null=True)
    discount_info = models.CharField(max_length=200, verbose_name=_("Discount Info"), blank=True, null=True, default='Up to 50% Off')
    description = models.TextField(verbose_name=_("Description"), blank=True, null=True)
    image = models.ImageField(upload_to=image_directory_path,  verbose_name=_("Campaign Image"))
    link = models.URLField(max_length=500, verbose_name=_("Link"), blank=True, null=True, help_text=_("Optional: URL to redirect when the banner is clicked."))
    order = models.PositiveIntegerField(default=0, verbose_name=_("Display Order"), help_text=_("Lower numbers will display first."))
    is_active = models.BooleanField(default=True, verbose_name=_("Is Active"), help_text=_("Toggle to show/hide the banner on the homepage."))
    
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, editable=False, help_text="This field is automatically set to the logged-in user.")
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = ['order',]  # Order by display order first, then newest

    def save(self, *args, **kwargs):
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title if self.title else f"Campaign {self.id}"

class About(models.Model):
    pass

class Contact(models.Model):
    pass





