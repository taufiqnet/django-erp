from django.contrib import admin
from .models import Company
from django.utils.html import mark_safe

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'company_logo', 'contact_number', 'email') 