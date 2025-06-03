# your_app/management/commands/update_reviews.py

import random
from django.core.management.base import BaseCommand
from core.models import Product

class Command(BaseCommand):
    help = "Update review_star and review_count for products"

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        updated = 0

        for product in products:
            if product.review_star is None:
                product.review_star = random.choice([4, 4.5, 5])
            if product.review_count is None:
                product.review_count = random.randint(50, 100)
            product.save()
            updated += 1

        self.stdout.write(f"Updated {updated} products with review_star and review_count.")

# run this command: python manage.py update_sold_count