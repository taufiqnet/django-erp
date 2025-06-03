from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from business.models import Business
from retail.models import Product
from .models import Contact
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from .models import Sale, SaleItem, Product

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import transaction
from django.utils.timezone import now
import json
from decimal import Decimal
from .models import Sale, SaleItem, Product

# def sales_view(request):
#     return render(request, 'retail/sale.html')

@login_required
def sales_view(request):
    products = Product.objects.filter(
        is_active=True, 
        business=request.user.profile.business
    ).select_related('category', 'unit', 'supplier')

    # Get customers for the current user's business
    customers = Contact.objects.filter(
        business=request.user.profile.business,  # or your business relationship
        type=Contact.ContactType.CUSTOMER,
        is_active=True
    ).order_by('first_name', 'last_name')

    context = {
        'products': products,
        'customers': customers,
        # ... other context data ...
    }

    return render(request, 'retail/sale.html', context)




@csrf_exempt
@login_required
def process_sale(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    try:
        with transaction.atomic():
            data = json.loads(request.body)
            items = data.get('items', [])
            
            if not items:
                return JsonResponse({'success': False, 'message': 'No items provided'}, status=400)

            business = request.user.profile.business

            # Handle customer (null allowed for walk-in)
            customer = None
            if data.get('customer_id'):
                try:
                    customer = Contact.objects.get(
                        id=data['customer_id'],
                        business=business,
                        is_active=True
                    )
                except Contact.DoesNotExist:
                    return JsonResponse(
                        {'success': False, 'message': 'Customer not found or inactive'},
                        status=400
                    )

            # Create the sale with basic info
            sale = Sale(
                business=business,
                customer=customer,
                created_by=request.user,
                updated_by=request.user,
                subtotal=0,
                vat_amount=0,
                grand_total=0
            )
            sale.save()

            # Process items
            for item in items:
                try:
                    product = Product.objects.select_for_update().get(
                        id=item['product_id'],
                        business=business,
                        is_active=True
                    )
                    quantity = int(item['quantity'])
                    price = Decimal(item['price'])

                    # Validate stock
                    if product.stock_quantity < quantity:
                        raise ValueError(f'Insufficient stock for {product.name}')

                    # Create sale item
                    SaleItem.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        price=price,
                        subtotal=quantity * price
                    )

                    # Update product stock
                    product.stock_quantity -= quantity
                    product.save()

                except Product.DoesNotExist:
                    return JsonResponse(
                        {'success': False, 'message': f'Product ID {item["product_id"]} not found or inactive'},
                        status=400
                    )
                except ValueError as e:
                    return JsonResponse(
                        {'success': False, 'message': str(e)},
                        status=400
                    )

            # Calculate and update totals
            sale.calculate_totals()
            sale.save()

            # Prepare response data
            response_data = {
                'success': True, 
                'invoice_number': sale.invoice_number,
                'sale_id': sale.id,
                'grand_total': str(sale.grand_total),
                'customer': {
                    'id': customer.id if customer else None,
                    'name': f"{customer.first_name} {customer.last_name}" if customer else 'Walk-in Customer'
                },
                'items': [
                    {
                        'product_id': item.product.id,
                        'name': item.product.name,
                        'quantity': item.quantity,
                        'price': str(item.price),
                        'subtotal': str(item.subtotal)
                    } for item in sale.items.all()
                ]
            }

            return JsonResponse(response_data)

    except json.JSONDecodeError:
        return JsonResponse(
            {'success': False, 'message': 'Invalid JSON data'},
            status=400
        )
    except Exception as e:
        return JsonResponse(
            {'success': False, 'message': f'An error occurred: {str(e)}'},
            status=500
        )

from django.db import transaction
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from .models import Contact, Business

def add_customer(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    try:
        
        business = request.user.profile.business 
        
        if not business:
            return JsonResponse({
                'success': False,
                'message': 'User is not associated with any business'
            }, status=400)

        with transaction.atomic():
            # Required fields
            first_name = request.POST.get('first_name')
            mobile = request.POST.get('mobile')
            
            if not first_name:
                return JsonResponse({'success': False, 'message': 'First name is required'}, status=400)
            if not mobile:
                return JsonResponse({'success': False, 'message': 'Mobile number is required'}, status=400)

            # Create customer
            customer = Contact(
                first_name=first_name,
                last_name=request.POST.get('last_name', ''),
                mobile=mobile,
                email=request.POST.get('email', ''),
                business=business,  # Use the business we fetched
                type=Contact.ContactType.CUSTOMER,
                address_line1=request.POST.get('address', ''),
                created_by=request.user,
                is_active=True
            )

            customer.full_clean()
            customer.save()

            return JsonResponse({
                'success': True,
                'id': customer.id,
                'contact_id': customer.contact_id,
                'cid': customer.cid,
                'first_name': customer.first_name,
                'last_name': customer.last_name,
                'mobile': customer.mobile,
                'email': customer.email,
                'address': customer.address_line1 or ''
            })

    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'message': 'Validation error',
            'errors': dict(e)
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        }, status=500)
    

# views.py
from django.http import JsonResponse
from .models import Contact

def customer_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)
    
    # Get the business ID - adjust based on your actual relationship
    business_id = request.GET.get('business_id') or request.user.business.id
    
    customers = Contact.objects.filter(
        business_id=business_id,
        type=Contact.ContactType.CUSTOMER,
        is_active=True
    ).values(
        'id',
        'contact_id',
        'first_name',
        'last_name',
        'mobile',
        'email',
        'address_line1'
    )
    
    return JsonResponse(list(customers), safe=False)




from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from .models import Sale, SaleItem, Product, Business
from datetime import datetime
import json

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Sale, Business
from datetime import datetime

@login_required
def sale_list(request):
    # Get the business for the logged in user through the profile
    business = get_object_or_404(Business, bid=request.user.profile.business.bid)
    
    # Get all sales for this business
    sales = Sale.objects.filter(business=business).order_by('-date')
    
    # Apply filters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    invoice = request.GET.get('invoice')
    
    if date_from:
        date_from = datetime.strptime(date_from, '%Y-%m-%d')
        sales = sales.filter(date__gte=date_from)
    
    if date_to:
        date_to = datetime.strptime(date_to, '%Y-%m-%d')
        sales = sales.filter(date__lte=date_to)
    
    if invoice:
        sales = sales.filter(invoice_number__icontains=invoice)
    
    # Pagination
    paginator = Paginator(sales, 25)  # Show 25 sales per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'sales': page_obj,
        'business': business,
    }
    return render(request, 'retail/sale_list.html', context)

@login_required
def sale_detail(request, sale_id):
    business = get_object_or_404(Business, bid=request.user.profile.business.bid)
    sale = get_object_or_404(Sale, id=sale_id, business=business)
    
    context = {
        'sale': sale,
        'business': business,
    }
    return render(request, 'retail/sale_detail.html', context)

@login_required
def print_receipt(request, sale_id):
    business = get_object_or_404(Business, bid=request.user.profile.business.bid)
    sale = get_object_or_404(Sale, id=sale_id, business=business)
    
    context = {
        'sale': sale,
        'business': business,
    }
    return render(request, 'retail/receipt_print.html', context)