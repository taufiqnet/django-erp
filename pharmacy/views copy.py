# views.py
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Product, Category, Customer, Sale, Batch, SaleItem
from django.views.decorators.http import require_POST

def sale_view(request):
    products = Product.objects.filter(is_active=True).select_related('category')
    categories = Category.objects.filter(is_active=True)
    return render(request, 'pharmacy/sale.html', {
        'products': products,
        'categories': categories
    })

@require_http_methods(["GET"])
def search_products(request):
    query = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    
    products = Product.objects.filter(is_active=True)
    
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(generic_name__icontains=query) |
            Q(barcode__icontains=query) |
            Q(ndc__icontains=query)
        )
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    return render(request, 'pharmacy/partials/product_list.html', {
        'products': products[:20]  # Limit to 20 results for performance
    })

from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest

@require_http_methods(["POST"])
def add_to_cart(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        batch = product.batches.first()
        
        if not batch:
            return HttpResponseBadRequest("Product has no available batches")
        
        # Initialize cart if not exists
        if 'cart' not in request.session:
            request.session['cart'] = {}
        
        cart = request.session['cart']
        
        # Get or initialize cart item
        cart_item = cart.get(str(product_id), {
            'quantity': 0,
            'unit_price': float(batch.selling_price),
            'total': 0,
            'tax_rate': product.get_tax_rate(),  # Make sure this method exists
            'discount_percent': 0,
            'batch_id': batch.id  # Important for later reference
        })
        
        # Update quantities
        cart_item['quantity'] += 1
        cart_item['total'] = cart_item['quantity'] * cart_item['unit_price']
        cart[str(product_id)] = cart_item
        
        # Explicitly mark session as modified
        request.session.modified = True
        
        # Update totals
        update_cart_totals(request)  # Make sure this exists
        
        # Return the rendered partial
        return render(request, 'pharmacy/partials/cart_items.html', {
            'sale_items': get_cart_items(request)  # Make sure this exists
        })
    
    
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error adding to cart: {str(e)}")
        return HttpResponseBadRequest("Error adding item to cart")

def update_cart_totals(request):
    cart = request.session.get('cart', {})
    subtotal = sum(item['total'] for item in cart.values())
    tax = sum(item['total'] * item.get('tax_rate', 0)/100 for item in cart.values())
    discount = sum(item['total'] * item.get('discount_percent', 0)/100 for item in cart.values())
    
    request.session['cart_subtotal'] = float(subtotal)
    request.session['cart_tax'] = float(tax)
    request.session['cart_discount'] = float(discount)
    request.session['cart_total'] = float(subtotal + tax - discount)
    request.session['sale_items_count'] = len(cart)

@require_POST
def update_cart_item(request, product_id):
    """Update quantity of a specific item in the cart"""
    try:
        new_quantity = int(request.POST.get('quantity', 1))
        if new_quantity < 1:
            raise ValueError("Quantity must be at least 1")
        
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str not in cart:
            return JsonResponse({'success': False, 'message': 'Product not in cart'}, status=404)
        
        # Get product details
        product = Product.objects.get(id=product_id)
        batch = product.batches.first()
        
        # Update cart item
        cart_item = cart[product_id_str]
        cart_item['quantity'] = new_quantity
        cart_item['total'] = new_quantity * cart_item['unit_price']
        cart[product_id_str] = cart_item
        
        request.session['cart'] = cart
        update_cart_totals(request)
        
        return render(request, 'pharmacy/partials/cart_items.html', {
            'sale_items': get_cart_items(request)
        })
        
    except ValueError as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error updating cart: {str(e)}'}, status=500)

@require_POST
def remove_from_cart(request, product_id):
    """Remove an item completely from the cart"""
    try:
        cart = request.session.get('cart', {})
        product_id_str = str(product_id)
        
        if product_id_str not in cart:
            return JsonResponse({'success': False, 'message': 'Product not in cart'}, status=404)
        
        # Remove the item
        del cart[product_id_str]
        request.session['cart'] = cart
        update_cart_totals(request)
        
        return render(request, 'pharmacy/partials/cart_items.html', {
            'sale_items': get_cart_items(request)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error removing from cart: {str(e)}'}, status=500)

def get_cart_items(request):
    # Helper function to get cart items with product details
    cart = request.session.get('cart', {})
    items = []
    
    for product_id, quantity in cart.items():
        product = Product.objects.get(id=product_id)
        batch = product.batches.first()  # Simplified - you might want more logic here
        
        items.append({
            'id': product_id,
            'product': product,
            'batch': batch,
            'quantity': quantity,
            'unit_price': batch.selling_price if batch else 0,
            'total': (batch.selling_price if batch else 0) * quantity
        })
    
    return items

@require_POST
def complete_sale(request):
    # Get cart from session
    cart = request.session.get('cart', {})
    
    if not cart:
        return render(request, 'pharmacy/partials/sale_result.html', {
            'success': False,
            'message': 'Cannot complete sale: Cart is empty'
        })
    
    try:
        # 1. Create Sale record
        sale = Sale.objects.create(
            business=request.user.business,
            customer=Customer.objects.filter(contact__user=request.user).first(),
            status='completed',
            subtotal=request.session.get('cart_subtotal', 0),
            tax_amount=request.session.get('cart_tax', 0),
            discount_amount=request.session.get('cart_discount', 0),
            total=request.session.get('cart_total', 0),
            created_by=request.user
        )
        
        # 2. Create SaleItems
        for product_id, item_data in cart.items():
            product = Product.objects.get(id=product_id)
            batch = Batch.objects.filter(product=product).first()
            
            SaleItem.objects.create(
                sale=sale,
                product=product,
                batch=batch,
                quantity=item_data['quantity'],
                unit_price=item_data['unit_price'],
                discount_percent=item_data.get('discount_percent', 0),
                tax_rate=item_data.get('tax_rate', 0),
                total=item_data['total']
            )
        
        # 3. Clear the cart
        clear_cart_data(request)
        
        # 4. Return success response
        return render(request, 'pharmacy/partials/sale_result.html', {
            'success': True,
            'sale_number': sale.sale_number,
            'total': sale.total
        })
        
    except Exception as e:
        return render(request, 'pharmacy/partials/sale_result.html', {
            'success': False,
            'message': f'Error completing sale: {str(e)}'
        })

@require_POST
def clear_cart(request):
    clear_cart_data(request)
    return render(request, 'pharmacy/partials/cart_items.html', {
        'sale_items': [],
        'cart_subtotal': 0,
        'cart_tax': 0,
        'cart_discount': 0,
        'cart_total': 0
    })

def clear_cart_data(request):
    """Helper function to clear cart session data"""
    keys = ['cart', 'cart_subtotal', 'cart_tax', 'cart_discount', 'cart_total', 'sale_items_count']
    for key in keys:
        if key in request.session:
            del request.session[key]