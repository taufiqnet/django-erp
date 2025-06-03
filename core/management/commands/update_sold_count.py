# your_app/management/commands/update_sold_count.py

import random
from django.core.management.base import BaseCommand
from core.models import Product

class Command(BaseCommand):
    help = 'Update sold_count for products with missing sold_count'

    def handle(self, *args, **kwargs):
        products = Product.objects.filter(sold_count__isnull=True)

        count = 0
        for product in products:
            product.sold_count = str(random.randint(200, 500))
            product.save()
            count += 1

        self.stdout.write(f'Updated sold_count for {count} products.')

# run this command: python manage.py update_sold_count