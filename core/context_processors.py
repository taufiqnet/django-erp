from .models import Category, Vendor, Product, ProductImage, CartOrder, CartOrderItems, ProductReview, Wishlist, Address

def default(request):
    categories = Category.objects.all()

    return {
        'categories': categories,
    }