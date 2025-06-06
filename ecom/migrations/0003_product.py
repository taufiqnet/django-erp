# Generated by Django 5.1.3 on 2025-06-02 05:21

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('business', '0001_initial'),
        ('contact', '0001_initial'),
        ('ecom', '0002_unit'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('short_description', models.TextField(blank=True, max_length=160, null=True)),
                ('sku', models.CharField(editable=False, max_length=50, unique=True, verbose_name='SKU')),
                ('upc', models.CharField(blank=True, max_length=50, null=True, unique=True, verbose_name='UPC/EAN')),
                ('barcode', models.CharField(blank=True, editable=False, max_length=100, null=True)),
                ('type', models.CharField(choices=[('simple', 'Simple Product'), ('variable', 'Variable Product'), ('composite', 'Composite Product')], default='simple', max_length=20)),
                ('price', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(0)])),
                ('cost_price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('original_price', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, validators=[django.core.validators.MinValueValidator(0)])),
                ('tax_type', models.CharField(choices=[('exempt', 'Tax Exempt'), ('standard', 'Standard Rate'), ('reduced', 'Reduced Rate'), ('zero', 'Zero Rate')], default='standard', max_length=20)),
                ('tax_rate', models.DecimalField(decimal_places=2, default=0, max_digits=5)),
                ('stock_quantity', models.DecimalField(decimal_places=3, default=0, max_digits=12)),
                ('low_stock_threshold', models.PositiveIntegerField(default=10)),
                ('manage_stock', models.BooleanField(default=True)),
                ('stock_status', models.CharField(choices=[('in_stock', 'In Stock'), ('out_of_stock', 'Out of Stock'), ('backorder', 'Available on Backorder')], default='in_stock', max_length=20)),
                ('weight', models.DecimalField(blank=True, decimal_places=3, max_digits=10, null=True)),
                ('height', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('width', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('length', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('requires_shipping', models.BooleanField(default=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='ecomproducts/')),
                ('gallery', models.JSONField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_featured', models.BooleanField(default=False)),
                ('is_bestseller', models.BooleanField(default=False)),
                ('is_new', models.BooleanField(default=True)),
                ('meta_title', models.CharField(blank=True, max_length=100, null=True)),
                ('meta_description', models.TextField(blank=True, null=True)),
                ('meta_keywords', models.CharField(blank=True, max_length=255, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ecom_product', to='business.business')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='ecom.category')),
                ('created_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_products_ecom', to=settings.AUTH_USER_MODEL)),
                ('related_products', models.ManyToManyField(blank=True, to='ecom.product')),
                ('supplier', models.ForeignKey(blank=True, limit_choices_to={'type': 'supplier'}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ecom_product_supplier', to='contact.contact')),
                ('unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='ecom.unit')),
                ('updated_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='updated_products_ecom', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Product',
                'verbose_name_plural': 'Products',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['sku'], name='ecom_produc_sku_be9fb9_idx'), models.Index(fields=['upc'], name='ecom_produc_upc_57eb70_idx'), models.Index(fields=['name'], name='ecom_produc_name_485324_idx'), models.Index(fields=['business', 'is_active'], name='ecom_produc_busines_cd9b8d_idx'), models.Index(fields=['category'], name='ecom_produc_categor_4210eb_idx')],
            },
        ),
    ]
