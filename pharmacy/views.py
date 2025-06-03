# views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Product, Category, Customer, Sale, Batch, SaleItem
from django.views.decorators.http import require_POST
# views.py - Fixed version with proper error handling and session management

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from decimal import Decimal
import json
from django.db.models import Q, Sum, F
import logging

logger = logging.getLogger(__name__)


def sale_view(request):
    """Simplified sales page view"""
    try:
        # Get products that have inventory
        products = Product.objects.prefetch_related('batches').all()
        for product in products:
            # Get first available batch for each product
            product.available_batch = product.batches.filter(quantity__gt=0).order_by('expiry_date').first()
        
        logger.debug(f"Products with stock found: {products.count()}")
        
        context = {
            'products': products,
            'categories': Category.objects.all(),
            'cart_items': get_cart_display_items(request),
            'cart_summary': get_cart_summary(request)
        }
        
        return render(request, 'pharmacy/sale.html', context)
        
    except Exception as e:
        logger.error(f"Error in sale_view: {str(e)}")
        return render(request, 'pharmacy/sale.html', {'products': [], 'categories': []})
    

@require_http_methods(["POST"])
def add_to_cart(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        batch = product.batches.filter(quantity__gt=0).order_by('expiry_date').first()
        
        if not batch:
            return JsonResponse(
                {'success': False, 'error': 'No available stock'},
                status=400
            )
        
        # Initialize or update cart
        cart = request.session.get('cart', {})
        product_key = str(product_id)
        
        if product_key in cart:
            cart[product_key]['quantity'] += 1
        else:
            cart[product_key] = {
                'product_id': product_id,
                'batch_id': batch.id,
                'quantity': 1,
                'unit_price': float(batch.selling_price),
                'tax_rate': getattr(product, 'tax_rate', 0),
                'discount_percent': 0,
            }
        
        # Update totals
        cart[product_key]['total'] = cart[product_key]['quantity'] * cart[product_key]['unit_price']
        
        # Save to session
        request.session['cart'] = cart
        request.session.modified = True
        
        return render(request, 'pharmacy/partials/cart_items.html', {
            'cart_items': get_cart_display_items(request),
            'cart_summary': get_cart_summary(request)
        })
        
    except Exception as e:
        return JsonResponse(
            {'success': False, 'error': str(e)},
            status=400
        )


def get_cart_display_items(request):
    """Convert cart session data to display format with error handling"""
    cart = request.session.get('cart', {})
    items = []
    
    print(f"Raw cart data: {cart}")  # Debugging
    
    for product_id, item_data in cart.items():
        try:
            product = Product.objects.get(id=item_data['product_id'])
            
            item = {
                'product': product,
                'product_id': product_id,
                'quantity': item_data.get('quantity', 0),
                'unit_price': float(item_data.get('unit_price', 0)),
                'subtotal': float(item_data.get('subtotal', 0)),
                'total': float(item_data.get('total', 0)),
                'batch_id': item_data.get('batch_id'),
                'tax_rate': float(item_data.get('tax_rate', 0)),
                'discount_percent': float(item_data.get('discount_percent', 0))
            }
            
            # Calculate if not present (backward compatibility)
            if 'subtotal' not in item_data:
                item['subtotal'] = item['quantity'] * item['unit_price']
            if 'total' not in item_data:
                item['total'] = item['subtotal'] * (1 + item['tax_rate']/100) * (1 - item['discount_percent']/100)
            
            items.append(item)
            
        except Product.DoesNotExist:
            print(f"Product {item_data['product_id']} not found, removing from cart")
            continue
        except Exception as e:
            print(f"Error processing cart item {product_id}: {str(e)}")
            continue
            
    print(f"Processed cart items: {items}")  # Debugging
    return items

def get_cart_summary(request):
    """Get cart summary data"""
    cart = request.session.get('cart', {})
    
    subtotal = sum(item['subtotal'] for item in cart.values())
    tax_total = sum(item.get('tax_amount', 0) for item in cart.values())
    discount_total = sum(item.get('discount_amount', 0) for item in cart.values())
    total = subtotal + tax_total - discount_total
    
    return {
        'subtotal': subtotal,
        'tax_total': tax_total,
        'discount_total': discount_total,
        'total': total,
        'items_count': sum(item['quantity'] for item in cart.values())
    }


@require_http_methods(["POST"])
def remove_from_cart(request, product_id):
    """Remove item from cart"""
    try:
        if 'cart' in request.session:
            cart = request.session['cart']
            product_key = str(product_id)
            
            if product_key in cart:
                del cart[product_key]
                request.session['cart'] = cart
                request.session['sale_items_count'] = sum(item['quantity'] for item in cart.values())
                request.session['sale_total'] = sum(item['total'] for item in cart.values())
                request.session.modified = True
        
        context = {
            'cart_items': get_cart_display_items(request),
            'cart_summary': get_cart_summary(request)
        }
        
        return render(request, 'pharmacy/partials/cart_items.html', context)
        
    except Exception as e:
        return HttpResponseBadRequest(f"Error removing item: {str(e)}")


@require_http_methods(["POST"])
def update_cart_quantity(request, product_id):
    """Update quantity of item in cart"""
    try:
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            return remove_from_cart(request, product_id)
        
        if 'cart' in request.session:
            cart = request.session['cart']
            product_key = str(product_id)
            
            if product_key in cart:
                cart[product_key]['quantity'] = quantity
                cart[product_key]['subtotal'] = quantity * cart[product_key]['unit_price']
                cart[product_key]['total'] = cart[product_key]['subtotal']
                
                request.session['cart'] = cart
                request.session['sale_items_count'] = sum(item['quantity'] for item in cart.values())
                request.session['sale_total'] = sum(item['total'] for item in cart.values())
                request.session.modified = True
        
        context = {
            'cart_items': get_cart_display_items(request),
            'cart_summary': get_cart_summary(request)
        }
        
        return render(request, 'pharmacy/partials/cart_items.html', context)
        
    except Exception as e:
        return HttpResponseBadRequest(f"Error updating quantity: {str(e)}")


@require_http_methods(["POST"])
def clear_cart(request):
    """Clear all items from cart"""
    try:
        request.session['cart'] = {}
        request.session['sale_items_count'] = 0
        request.session['sale_total'] = 0
        request.session.modified = True
        
        context = {
            'cart_items': [],
            'cart_summary': get_cart_summary(request)
        }
        
        return render(request, 'pharmacy/partials/cart_items.html', context)
        
    except Exception as e:
        return HttpResponseBadRequest(f"Error clearing cart: {str(e)}")


# Additional utility functions you might need

def search_products(request):
    """Search products with HTMX"""
    search_query = request.GET.get('search', '').strip()
    category_id = request.GET.get('category', '')
    
    products = Product.objects.all()
    
    if search_query:
        products = products.filter(name__icontains=search_query)
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    products = products.select_related('category').prefetch_related('batches')
    
    context = {
        'products': products,
        'search_query': search_query
    }
    
    return render(request, 'pharmacy/partials/product_list.html', context)


def filter_products(request):
    """Filter products by category"""
    return search_products(request)  # Same logic


@require_http_methods(["POST"])
def complete_sale(request):
    """Complete the sale transaction"""
    try:
        cart = request.session.get('cart', {})
        
        if not cart:
            return HttpResponseBadRequest("Cart is empty")
        
        # Here you would implement your sale completion logic
        # For example, create Sale and SaleItem records
        
        # Clear cart after successful sale
        request.session['cart'] = {}
        request.session['sale_items_count'] = 0
        request.session['sale_total'] = 0
        request.session.modified = True
        
        return HttpResponse('''
            <div class="bg-green-100 border border-green-400 text-green-700 px-3 py-2 rounded text-sm">
                Sale completed successfully!
            </div>
        ''')
        
    except Exception as e:
        return HttpResponseBadRequest(f"Error completing sale: {str(e)}")