from urllib import request
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Count
from taggit.models import Tag
from company.models import Company
from core.models import Category, Vendor, Product, ProductImage, CartOrder, CartOrderItems, ProductReview, Wishlist, PaymentMethod, Brand
from page.models import Banner, Ads, Campaign
from django.db.models import Q



def index(request):
    # Fetch the first 20 published and featured products
    beauty_products = Product.objects.filter(product_status='published', featured=True, business_type='beauty').order_by('?')[:18]

    # Utility function to get subcategory IDs
    def get_all_subcategory_ids(category):
        """Recursively fetch all subcategory IDs for a given category."""
        subcategory_ids = []
        subcategories = category.subcategories.all()
        for subcategory in subcategories:
            subcategory_ids.append(subcategory.id)
            subcategory_ids.extend(get_all_subcategory_ids(subcategory))
        return subcategory_ids

    # Fetch the main category for K-Beauty
    k_beauty_category = Category.objects.filter(slug='k-beauty', parent__isnull=True).first()

    if k_beauty_category:
        # Collect all subcategory IDs under the main category
        subcategory_ids = get_all_subcategory_ids(k_beauty_category)
        # Include the main category ID
        subcategory_ids.append(k_beauty_category.id)

        # Fetch products under the main category and its subcategories
        korean_products = Product.objects.filter(
            product_status='published',
            business_type='beauty',
            category_id__in=subcategory_ids  # Filter by category and subcategories
        ).order_by('?')[:18]
    else:
        korean_products = Product.objects.none()  # No products if "K-Beauty" doesn't exist

    # Fetch random beauty products
    bridal_products = Product.objects.filter(
        product_status='published',
        featured=True,
        business_type='beauty'
    ).order_by('?')[:18]  # Randomize and limit to 18 products

    # Fetch only top-level categories (main categories)
    parent_categories = Category.objects.filter(parent__isnull=True, business_type='beauty')


    # Get only subcategories (categories with a parent)
    subcategories = Category.objects.filter(parent__isnull=False, business_type='beauty').order_by('title')

    # Fetch active banners ordered by their order field
    banners = Banner.objects.filter(is_active=True, type='beauty').order_by('order')

    # Fetch active advertisements ordered by their order field
    ads = Ads.objects.filter(is_active=True, type='beauty').order_by('order')[:2]

    # Fetch active campaign ordered by their order field
    campaigns = Campaign.objects.filter(is_active=True, type='beauty').order_by('order')

    brands = Brand.objects.filter(status=True, business_type='beauty').order_by('?')

    company = Company.objects.first()  # Assuming you have one active company

    context = {
        'parent_categories': parent_categories,
        'subcategories': subcategories,
        'beauty_products': beauty_products,
        'korean_products': korean_products,  
        'bridal_products': bridal_products,  
        'banners': banners,  # banners to the context
        'ads': ads,  # advertisements in the context
        'campaigns': campaigns,  # campaigns in the context
        'brands': brands,  # campaigns in the context
        'company': company,
    }

    return render(request, "core/index.html", context)


# Multivendor Index Page
# This function is responsible for multivendor Shop index page as 'Daraz'.
# After implementation the will be index page instead of above index page.
def multivendorIndex(request):
    # Fetch the first 20 published and featured products
    products = Product.objects.filter(product_status='published')[:18]

    # Fetch categories with product counts
    parent_categories = Category.objects.filter(parent__isnull=True)

    # Fetch active banners ordered by their order field
    banners = Banner.objects.filter(is_active=True).order_by('order')

    # Fetch active advertisements ordered by their order field
    ads = Ads.objects.filter(is_active=True).order_by('order')[:2]

    # Fetch active campaign ordered by their order field
    campaigns = Campaign.objects.filter(is_active=True).order_by('order')

    context = {
        'parent_categories': parent_categories,
        'products': products,
        'banners': banners,  # banners to the context
        'ads': ads,  # advertisements in the context
        'campaigns': campaigns,  # campaigns in the context
    }

    return render(request, "core/multivendorIndex.html", context)



def business_type_food(request):

    grocery_products = Product.objects.filter(
        Q(category__title__icontains='rice') |
        Q(category__title__icontains='dal') |
        Q(category__title__icontains='mix') |
        Q(category__title__icontains='oil'),
        product_status='published',
        featured=True
    ).order_by('-title')[:14]

    fish_meat_veg_products  = Product.objects.filter(
        Q(category__title__icontains='fish') |
        Q(category__title__icontains='meat') |
        Q(category__title__icontains='vegetables'),
        product_status='published',
        featured=True
    ).order_by('-title')[:14]

    dairy_products  = Product.objects.filter(
        Q(category__title__icontains='milk') |
        Q(category__title__icontains='cheese') |
        Q(category__title__icontains='butter'),
        product_status='published',
        featured=True
    ).order_by('-title')[:14]

    snacks_products  = Product.objects.filter(
        Q(category__title__icontains='tea coffee') |
        Q(category__title__icontains='soup') |
        Q(category__title__icontains='noodles'),
        product_status='published',
        featured=True
    ).order_by('-title')[:14]

    cleaning_products  = Product.objects.filter(
        Q(category__title__icontains='laundry') |
        Q(category__title__icontains='cleaner'),
        product_status='published',
        featured=True
    ).order_by('-title')[:14]

    blank_cards = [None] * 3  # Generate 3 placeholders

    # Fetch categories with product counts
    parent_categories = Category.objects.filter(parent__isnull=True, business_type='food')

    # Get only subcategories (categories with a parent)
    subcategories = Category.objects.filter(parent__isnull=False, business_type='food').order_by('title')

    # Fetch active banners ordered by their order field
    banners = Banner.objects.filter(is_active=True, type='food').order_by('order')

    # Fetch active advertisements ordered by their order field
    ads = Ads.objects.filter(is_active=True, type='food').order_by('order')[:2]

    # Fetch active campaign ordered by their order field
    campaigns = Campaign.objects.filter(is_active=True, type='food').order_by('order')

    brands = Brand.objects.filter(status=True, business_type='food').order_by('?')

    context = {
        'parent_categories': parent_categories, 
        'subcategories': subcategories, 
        'grocery_products': grocery_products,  
        'fish_meat_veg_products': fish_meat_veg_products,  
        'dairy_products': dairy_products,  
        'snacks_products': snacks_products,  
        'cleaning_products': cleaning_products,
        'blank_cards': blank_cards,  # if product is blank
        'banners': banners,  # banners to the context
        'ads': ads,  # advertisements in the context
        'campaigns': campaigns,  # campaigns in the context
        'brands': brands,
    }

    return render(request, "core/food.html", context)


from django.shortcuts import render
from django.db.models import Q
from .models import Product

def product_list_view(request, business_type):
    category = request.GET.get('category', None)  # Get category from the URL query parameter

    # Filter rice, dal, oil, ready mix products by business type
    rice_dal_oil_products = Product.objects.filter(
        Q(category__title__icontains='rice') |
        Q(category__title__icontains='dal') |
        Q(category__title__icontains='oil') |
        Q(category__title__icontains='mix'),
        category__business_type=business_type,
        product_status='published'
    ).order_by('-title')[:28] if category == 'rice_dal_oil' else Product.objects.none()

    # Filter fish, meat, and vegetable products by business type
    fish_meat_veg_products = Product.objects.filter(
        Q(category__title__icontains='fish') |
        Q(category__title__icontains='meat') |
        Q(category__title__icontains='vegetables'),
        category__business_type=business_type,
        product_status='published'
    ).order_by('-title')[:14] if category == 'fish_meat_veg' else Product.objects.none()

    # Filter dairy products by business type
    dairy_products = Product.objects.filter(
        Q(category__title__icontains='milk') |
        Q(category__title__icontains='cheese') |
        Q(category__title__icontains='butter'),
        category__business_type=business_type,
        product_status='published'
    ).order_by('-title')[:28] if category == 'dairy' else Product.objects.none()

    # Filter snacks products by business type
    snacks_products = Product.objects.filter(
       Q(category__title__icontains='tea coffee') |
       Q(category__title__icontains='noodles') |
       Q(category__title__icontains='soup'),
       category__business_type=business_type,
       product_status='published'
    ).order_by('-title')[:28] if category == 'snacks' else Product.objects.none()

    # Filter cleaning products by business type
    cleaning_products = Product.objects.filter(
       Q(category__title__icontains='laundry') |
        Q(category__title__icontains='cleaner'),
        category__business_type=business_type,
        product_status='published'
    ).order_by('-title')[:28] if category == 'cleaning' else Product.objects.none()

    # Filter products by business type excluding the specific categories (fish, meat, vegetables, dairy)
    other_products = Product.objects.filter(
        ~Q(category__title__icontains='rice') &
        ~Q(category__title__icontains='dal') &
        ~Q(category__title__icontains='oil') &
        ~Q(category__title__icontains='mix') &
        ~Q(category__title__icontains='fish') &
        ~Q(category__title__icontains='meat') &
        ~Q(category__title__icontains='vegetables') &
        ~Q(category__title__icontains='milk') &
        ~Q(category__title__icontains='cheese') &
        ~Q(category__title__icontains='butter') &
        ~Q(category__title__icontains='tea') &
        ~Q(category__title__icontains='coffee') &
        ~Q(category__title__icontains='noodles') &
        ~Q(category__title__icontains='soup') &
        ~Q(category__title__icontains='laundry') &
        ~Q(category__title__icontains='cleaner'),
        category__business_type=business_type,
        product_status='published'
    ) if category is None else Product.objects.none()

    # Combine all filtered products for the context
    products = rice_dal_oil_products | fish_meat_veg_products | dairy_products | cleaning_products | snacks_products | other_products

    
    # Utility function to get subcategory IDs
    def get_all_subcategory_ids(category):
        """Recursively fetch all subcategory IDs for a given category."""
        subcategory_ids = []
        subcategories = category.subcategories.all()
        for subcategory in subcategories:
            subcategory_ids.append(subcategory.id)
            subcategory_ids.extend(get_all_subcategory_ids(subcategory))
        return subcategory_ids
    
    k_beauty_category = Category.objects.filter(slug='k-beauty', parent__isnull=True).first()

    if k_beauty_category:
        # Collect all subcategory IDs under the main category
        subcategory_ids = get_all_subcategory_ids(k_beauty_category)
        # Include the main category ID
        subcategory_ids.append(k_beauty_category.id)

        # Fetch products under the main category and its subcategories
        korean_products = Product.objects.filter(
            product_status='published',
            business_type='beauty',
            category_id__in=subcategory_ids  # Filter by category and subcategories
        ).order_by('?')
    else:
        korean_products = Product.objects.none()  # No products if "K-Beauty" doesn't exist

    beauty_products = korean_products

    # Get only subcategories (categories with a parent)
    subcategories = Category.objects.filter(parent__isnull=False, business_type='beauty').order_by('?')[:10]

    # Create a dynamic headline
    headline = f"{business_type.capitalize()} Products"

    context = {
        'products': products,
        'business_type': business_type,
        'headline': headline,
        'rice_dal_oil_products': rice_dal_oil_products,  # Specifically filtered rice, dal and oil products
        'fish_meat_veg_products': fish_meat_veg_products,  # Specifically filtered fish, meat, and vegetable products
        'dairy_products': dairy_products,  # Specifically filtered dairy products
        'snacks_products': snacks_products,  # Specifically filtered snacks products
        'cleaning_products': cleaning_products,  # Specifically filtered cleaing products
        'korean_products': korean_products,  # Specifically filtered korean products
        'category': category,  # Pass category to the template
        'subcategories': subcategories,  # Pass category to the template
    }
    return render(request, 'core/product-list.html', context)


# Multivendor product list
def multivendor_product_list_view(request):
    category = request.GET.get('category', None)

    products = Product.objects.filter(product_status='published')

    context = {
        'products': products,
        'category': category,
    }
    return render(request, 'core/m-product-list.html', context)



def category_list_view(request):
    categories = Category.objects.all().annotate(product_count=Count("product"))
    context = {
        'categories': categories
    }
    return render(request, "core/category-list.html", context) 
    


# def category_product_list_view(request, slug):
#     category = Category.objects.get(slug=slug)
#     products = Product.objects.filter(product_status='published', category=category)

#     context = {
#         'category': category,
#         'products': products
#     }
#     return render(request, "core/category-product-list.html", context) 


from django.shortcuts import get_object_or_404, render
from .models import Category, Product

def category_product_list_view(request, slug):
    # Fetch the category by slug (it can be a parent or a subcategory)
    category = get_object_or_404(Category, slug=slug)

    if category.parent is None:
        # If the category is a parent, get products for all its subcategories
        subcategories = Category.objects.filter(parent=category)
        products = Product.objects.filter(category__in=subcategories)
    else:
        # If it's a subcategory, get products directly associated with it
        products = Product.objects.filter(category=category)

    return render(
        request, 
        'core/category-product-list.html', 
        {'category': category, 'products': products}
    )




def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(slug=slug)

    # Getting all reviews
    reviews = ProductReview.objects.filter(product=product).order_by('-created_at')

    p_image = product.p_images.all()

    context = {
        'p': product,
        'p_images': p_image,
        'reviews': reviews,
        'related_products': related_products,
    }

    return render(request, "core/product-detail.html", context)

def tag_list_view(request, tag_slug=None):
    products = Product.objects.filter(product_status='published').order_by('-id') 

    tag = None
    if tag_slug:
        tag = get_object_or_404(Tag, slug=tag_slug)
        products = products.filter(tags__in=[tag])

    context = {
        "products": products,
        "tag": tag,
    }

    return render(request, 'core/tag.html', context)


from django.db.models import Q   
# Q object: Allows combining conditions using bitwise operators (| for OR, & for AND).

def search_view(request):
    query = request.GET.get('q')

    # Use Q to combine title and description with an OR condition
    products = Product.objects.filter(
        Q(title__icontains=query) | 
        Q(description__icontains=query) | 
        Q(brand__title__icontains=query) | 
        Q(category__title__icontains=query) | 
        Q(tags__name__icontains=query)
    ).distinct().order_by('title')

    # Show all subcategory in search results
    subcategories = Category.objects.filter(parent__isnull=False, business_type='beauty').order_by('?')[:10]


    context = {
        "products": products,
        "subcategories": subcategories,
        "query": query,
    }
    return render(request, 'core/search.html', context)


def add_to_cart(request):
    if request.method == "GET":
        product_id = request.GET.get('id')
        product_pid = request.GET.get('pid')
        product_image = request.GET.get('image')
        product_title = request.GET.get('title')
        product_price = request.GET.get('price')

        # Initialize cart if it doesn't exist
        if 'cart_data_obj' not in request.session:
            request.session['cart_data_obj'] = {}

        cart_data = request.session['cart_data_obj']

        # Add or update product in cart
        if product_id in cart_data:
            cart_data[product_id]['qty'] += 1
        else:
            cart_data[product_id] = {
                'pid': product_pid,
                'image': product_image,
                'title': product_title,
                'price': float(product_price),
                'qty': 1,
            }

        request.session['cart_data_obj'] = cart_data
        request.session.modified = True

        # Calculate total cart items
        total_cart_items = sum(item['qty'] for item in cart_data.values())

        return JsonResponse({
            'success': True,
            'totalcartitems': total_cart_items
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)


from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.db.models import Q
from uuid import uuid4
from core.models import CartOrder, ShippingAddress, CartOrderItems

from django.shortcuts import render, redirect
from django.db import transaction
from decimal import Decimal

# Constants for shipping charges
SHIPPING_CHARGES = {
    'inside_dhaka': 70.00,
    'outside_dhaka': 150.00,
}

def calculate_cart_totals(cart_data):
    """Calculate total price for the cart."""
    total_price = 0
    for key, item in cart_data.items():
        item['total'] = float(item['price']) * int(item['qty'])
        total_price += item['total']
    return total_price

def create_cart_order_and_items(user, guest_id, cart_data, total_price, shipping_charge, delivery_method, payment_method):
    """Create CartOrder and CartOrderItems."""
    with transaction.atomic():  # Ensures atomicity

        # Convert total_price to Decimal if it's a float
        total_price_decimal = Decimal(total_price) if isinstance(total_price, float) else total_price

        # Create CartOrder
        cart_order = CartOrder.objects.create(
            user=user,
            guest_id=guest_id,
            price=total_price_decimal + shipping_charge,  # Now both are Decimal
            shipping_fee=shipping_charge,
            delivery_method=delivery_method,
            payment_method=payment_method,
            paid_status=False,
        )

        # Create CartOrderItems
        for key, item in cart_data.items():
            CartOrderItems.objects.create(
                order=cart_order,
                invoice_no=f"INV-{uuid4().hex[:8].upper()}",
                product_status="in_review",
                item=item['title'],
                image=item['image'],
                qty=item['qty'],
                price=Decimal(item['price']),
                total=Decimal(item['total']),
            )
    return cart_order


def checkout_view(request):
    # Retrieve cart data
    cart_data = request.session.get('cart_data_obj', {})
    total_price = calculate_cart_totals(cart_data)
    request.session['cart_data_obj'] = cart_data

    user = request.user if request.user.is_authenticated else None
    guest_id = str(uuid4()) if not user else None
    payment_methods = PaymentMethod.objects.filter(is_enabled=True)

    if request.method == 'POST':
        # Extract and validate POST data
        try:
            name = request.POST['name']
            phone = request.POST['phone']
            city = request.POST['city']
            area = request.POST['area']
            address = request.POST['address']
            email = request.POST.get('email', None)
            order_note = request.POST.get('order_note', None)
            shipping_method = request.POST['shipping_method']
            payment_method_name = request.POST['payment_method']
        except KeyError:
            return render(request, 'core/checkout.html', {
                'error': 'Missing required fields',
                'cart_data': cart_data,
                'final': {'total_price': total_price, 'shipping_charge': 0, 'grand_total': 0},
                'payment_methods': payment_methods,
            })

        # Determine shipping charge and delivery method
        shipping_charge = Decimal(SHIPPING_CHARGES.get(
            'inside_dhaka' if shipping_method == 'inside' else 'outside_dhaka'
        ))  # Ensure shipping_charge is Decimal
        delivery_method = 'inside_dhaka' if shipping_method == 'inside' else 'outside_dhaka'

        # Fetch payment method
        try:
            payment_method = PaymentMethod.objects.get(name=payment_method_name)
        except PaymentMethod.DoesNotExist:
            return render(request, 'core/checkout.html', {
                'error': 'Invalid payment method selected',
                'cart_data': cart_data,
                'final': {'total_price': total_price, 'shipping_charge': shipping_charge, 'grand_total': total_price + shipping_charge},
                'payment_methods': payment_methods,
            })

        with transaction.atomic():  # Wrap in a transaction
            # Create CartOrder first
            cart_order = create_cart_order_and_items(
                user, guest_id, cart_data, total_price, shipping_charge, delivery_method, payment_method
            )

            # Create ShippingAddress and associate with the CartOrder
            shipping_address = ShippingAddress.objects.create(
                user=user,
                guest_id=guest_id,
                order=cart_order,  # Associate the CartOrder here
                name=name,
                phone=phone,
                city=city,
                area=area,
                address=address,
                email=email,
                order_note=order_note,
            )

        # Clear the cart after order is placed
        request.session.pop('cart_data_obj', None)

        # Redirect to the order confirmation page
        return redirect('core:order_confirmation', order_id=cart_order.id)

    context = {
        'cart_data': cart_data,
        'final': {
            'total_price': total_price,
            'shipping_charge': Decimal(SHIPPING_CHARGES['inside_dhaka']),  # Ensure shipping_charge is Decimal
            'grand_total': Decimal(total_price) + Decimal(SHIPPING_CHARGES['inside_dhaka']),  # Convert to Decimal
        },
        'payment_methods': payment_methods,
    }

    if guest_id:
        guest_shipping_address = ShippingAddress.objects.filter(guest_id=guest_id).last()
        context['guest_shipping_address'] = guest_shipping_address

    return render(request, 'core/checkout.html', context)





from django.views.decorators.csrf import csrf_exempt

@csrf_exempt

def update_cart(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        action = request.POST.get("action")

        # Ensure the session cart exists
        if 'cart_data_obj' in request.session:
            cart_data = request.session['cart_data_obj']
            
            if product_id in cart_data:
                if action == "increase":
                    cart_data[product_id]['qty'] = int(cart_data[product_id]['qty']) + 1
                
                elif action == "decrease":
                    current_qty = int(cart_data[product_id]['qty'])
                    if current_qty > 1:
                        cart_data[product_id]['qty'] = current_qty - 1
                    else:
                        # If quantity is 1 and decrease is clicked, remove the item
                        del cart_data[product_id]
                
                elif action == "delete":
                    # Directly remove the product from the cart
                    del cart_data[product_id]

                # Save the updated cart back to the session
                request.session['cart_data_obj'] = cart_data
                request.session.modified = True

                # Calculate total cart items
                total_cart_items = sum(item['qty'] for item in cart_data.values())

                return JsonResponse({
                    "success": True,
                    "cart_data": request.session['cart_data_obj'],
                    "total_cart_items": total_cart_items
                })

        return JsonResponse({
            "success": False,
            "message": "Product not found in cart or invalid action"
        }, status=400)

    return JsonResponse({"success": False, "message": "Invalid request method"}, status=400)


from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from .models import CartOrder, CartOrderItems

def order_confirmation(request, order_id):
    order = get_object_or_404(CartOrder, id=order_id)
    order_items = CartOrderItems.objects.filter(order=order)

    # Ensure payment_method exists and get the display name correctly
    # payment_method_display = order.payment_method.get_payment_method_display() if order.payment_method else None

    context = {
        'order': order,
        'order_items': order_items,
        'shipping_fee': order.shipping_fee,
        # 'payment_method': payment_method_display,  # Use the human-readable method
    }
    return render(request, 'core/order_confirmation.html', context)






from reportlab.pdfgen import canvas
from django.http import HttpResponse

def download_invoice(request, order_id):
    order = get_object_or_404(CartOrder, id=order_id)
    order_items = CartOrderItems.objects.filter(order=order)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'

    p = canvas.Canvas(response)
    p.drawString(100, 800, "Invoice")
    p.drawString(100, 780, f"Order ID: {order.id}")
    p.drawString(100, 760, f"Date: {order.order_date}")
    p.drawString(100, 740, f"Total: ${order.price}")
    
    y = 700
    for item in order_items:
        p.drawString(100, y, f"{item.item} - {item.qty} x ${item.price}")
        y -= 20

    p.showPage()
    p.save()
    return response
