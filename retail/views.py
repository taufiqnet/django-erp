from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from business.models import Business
from retail.models import Product, Sale, SaleItem, Payment
from .models import Contact
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.db import transaction
from decimal import Decimal
from django.contrib import messages
import logging
logger = logging.getLogger(__name__)

# def sales_view(request):
#     return render(request, 'retail/sale.html')

@login_required
def sales_view(request):
    products = Product.objects.filter(
        is_active=True,
        business=request.user.profile.business
    ).select_related('category', 'unit', 'supplier')

    customers = Contact.objects.filter(
        business=request.user.profile.business,
        type=Contact.ContactType.CUSTOMER,
        is_active=True
    ).order_by('first_name', 'last_name')

    payment_methods = Sale.PAYMENT_METHODS

    context = {
        'products': products,
        'customers': customers,
        'payment_methods': payment_methods,
    }
    return render(request, 'retail/sale.html', context)


from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from decimal import Decimal
import json

@csrf_exempt
@login_required
def process_sale(request): # Removed duplicate @csrf_exempt
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

    try:
        with transaction.atomic():
            data = json.loads(request.body)
            items = data.get('items', [])

            if not items:
                return JsonResponse({'success': False, 'message': 'No items provided'}, status=400)

            business = request.user.profile.business
            customer = None

            customer_id_str = data.get('customer_id')
            if customer_id_str:
                try:
                    customer = Contact.objects.get(
                        id=customer_id_str,
                        business=business,
                        is_active=True
                    )
                except Contact.DoesNotExist:
                    return JsonResponse(
                        {'success': False, 'message': 'Customer not found or inactive'},
                        status=400
                    )

            sale = Sale(
                business=business,
                customer=customer,
                created_by=request.user,
                updated_by=request.user, # Should be request.user initially
                payment_method=data.get('payment_method', 'cash'),
                discount_amount=Decimal(data.get('discount_amount', 0)) # This is a fixed amount for new sales via API
            )
            # discount_percent might be more suitable if items are also posted to calculate from subtotal
            sale.save() # Initial save to get sale ID for items

            for item_data in items: # Renamed item to item_data for clarity
                try:
                    product = Product.objects.get(
                        id=item_data['product_id'],
                        business=business,
                        is_active=True
                    )

                    sale_item = SaleItem(
                        sale=sale,
                        product=product,
                        quantity=Decimal(item_data['quantity']),
                        price=Decimal(item_data['price']),
                        tax_rate=Decimal(item_data.get('tax_rate', product.tax_rate)), # Default to product's tax_rate
                        tax_type=item_data.get('tax_type', product.tax_type) # Default to product's tax_type
                    )
                    # SaleItem's save method will calculate its own subtotal
                    sale_item.save()

                    if product.manage_stock:
                        product.stock_quantity -= sale_item.quantity
                        product.save()

                except Product.DoesNotExist:
                    # Transaction will roll back
                    return JsonResponse(
                        {'success': False, 'message': f'Product ID {item_data.get("product_id")} not found'},
                        status=400
                    )
                except KeyError as e:
                    return JsonResponse(
                        {'success': False, 'message': f'Missing data in item: {str(e)}'},
                        status=400
                    )

            sale.calculate_totals() # Recalculate totals for the Sale based on all SaleItems
            # sale.save() is called within calculate_totals()

            amount_paid_from_request = Decimal(data.get('amount_paid', 0))
            if amount_paid_from_request > 0:
                Payment.objects.create(
                    sale=sale,
                    amount=amount_paid_from_request,
                    payment_method=sale.payment_method, # Or data.get('payment_method') from payload
                    created_by=request.user,
                    status='completed'
                )
            # The Payment.save() method updates sale.amount_paid and sale.payment_status
            # and then saves the sale object.

            return JsonResponse({
                'success': True,
                'invoice_number': sale.invoice_number,
                'grand_total': str(sale.grand_total)
            })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'}, status=400)
    except Exception as e:
        logger.error(f"Error processing sale: {str(e)}", exc_info=True)
        return JsonResponse(
            {'success': False, 'message': f'An unexpected error occurred: {str(e)}'},
            status=500
        )

from django.core.exceptions import ValidationError
# Contact, Business already imported

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
            first_name = request.POST.get('first_name')
            mobile = request.POST.get('mobile')

            if not first_name:
                return JsonResponse({'success': False, 'message': 'First name is required'}, status=400)
            if not mobile:
                return JsonResponse({'success': False, 'message': 'Mobile number is required'}, status=400)

            customer = Contact(
                first_name=first_name,
                last_name=request.POST.get('last_name', ''),
                mobile=mobile,
                email=request.POST.get('email', ''),
                business=business,
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
        error_messages = []
        for field, errors in e.message_dict.items():
            error_messages.extend(errors)
        return JsonResponse({
            'success': False,
            'message': 'Validation error: ' + ", ".join(error_messages),
            'errors': e.message_dict
        }, status=400)
    except Exception as e:
        logger.error(f"Error adding customer: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'An unexpected error occurred: {str(e)}'
        }, status=500)


# from .models import Contact # Already imported

def customer_list(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Not authenticated'}, status=401)

    try:
        business = request.user.profile.business
        if not business:
             return JsonResponse({'error': 'User not associated with a business'}, status=400)
        business_id = business.id
    except AttributeError:
        return JsonResponse({'error': 'Business profile not found for user'}, status=400)

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


# Django specific imports already at the top
from django.core.paginator import Paginator
from datetime import datetime

@login_required
def sale_list(request):
    try:
        business = request.user.profile.business
    except Business.DoesNotExist:
        messages.error(request, "Business information not found for your profile.")
        return redirect('some_error_page_or_dashboard') # Redirect to a relevant page

    sales_qs = Sale.objects.filter(business=business).select_related('customer').order_by('-date')

    date_from_str = request.GET.get('date_from')
    date_to_str = request.GET.get('date_to')
    invoice_query = request.GET.get('invoice')

    if date_from_str:
        try:
            date_from_obj = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            sales_qs = sales_qs.filter(date__gte=date_from_obj)
        except ValueError:
            messages.warning(request, f"Invalid 'date from' format: {date_from_str}. Please use YYYY-MM-DD.")

    if date_to_str:
        try:
            date_to_obj = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            sales_qs = sales_qs.filter(date__lte=date_to_obj)
        except ValueError:
            messages.warning(request, f"Invalid 'date to' format: {date_to_str}. Please use YYYY-MM-DD.")

    if invoice_query:
        sales_qs = sales_qs.filter(invoice_number__icontains=invoice_query)

    paginator = Paginator(sales_qs, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'sales': page_obj,
        'business': business,
        'date_from_val': date_from_str,
        'date_to_val': date_to_str,
        'invoice_val': invoice_query,
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


@login_required
def sale_edit(request, pk):
    business = request.user.profile.business
    sale = get_object_or_404(Sale, pk=pk, business=business)

    customers = Contact.objects.filter(business=business, type=Contact.ContactType.CUSTOMER, is_active=True)
    # Products for dropdown, ensure it's specific to the business
    products_for_dropdown = Product.objects.filter(business=business, is_active=True)
    payment_methods = Sale.PAYMENT_METHODS

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update basic sale info from form
                customer_id_str = request.POST.get('customer'); current_total_paid_on_sale_load = sale.amount_paid # HACK: Combined line
                if customer_id_str:
                    # Ensure customer belongs to the same business for security
                    sale.customer = get_object_or_404(Contact, pk=customer_id_str, business=business, type=Contact.ContactType.CUSTOMER)
                else:
                    sale.customer = None

                sale.date = request.POST.get('date')
                sale.payment_method = request.POST.get('payment_method')
                sale.discount_percent = Decimal(request.POST.get('discount', 0))
                # sale.amount_paid = Decimal(request.POST.get('amount_paid', 0)) # Removed direct assignment

                new_total_amount_paid_from_form = Decimal(request.POST.get('amount_paid', 0))
                if new_total_amount_paid_from_form > current_total_paid_on_sale_load:
                    additional_payment_amount = new_total_amount_paid_from_form - current_total_paid_on_sale_load
                    if additional_payment_amount > Decimal('0.00'):
                        Payment.objects.create(
                            sale=sale,
                            amount=additional_payment_amount,
                            payment_method=request.POST.get('payment_method', sale.payment_method),
                            created_by=request.user,
                            status='completed'
                        )

                # The Sale model's save() method correctly updates is_paid/payment_status based on amounts.
                # Direct setting of 'is_paid' from form can be tricky if not coordinated with model logic.
                # For example: sale.is_paid = request.POST.get('is_paid') == 'true'

                submitted_products_ids = request.POST.getlist('product')

                # Only modify items if product data was actually submitted and is not empty.
                if submitted_products_ids and any(pid for pid in submitted_products_ids if pid.strip()):
                    new_sale_items_data = []
                    submitted_prices = request.POST.getlist('price')
                    submitted_quantities = request.POST.getlist('quantity')

                    if not (len(submitted_products_ids) == len(submitted_prices) == len(submitted_quantities)):
                        messages.error(request, "Mismatch in submitted item data counts. Please check items.")
                        raise ValueError("Item data lists length mismatch")

                    for i, product_id_str in enumerate(submitted_products_ids):
                        if not product_id_str.strip():
                            # Handle cases where a row might be submitted with no product selected
                            if submitted_prices[i].strip() or submitted_quantities[i].strip(): # if other fields have data, it's an error
                                messages.error(request, f"Missing product for item {i+1} but other data present.")
                                raise ValueError(f"Missing product for item {i+1}")
                            continue # Skip if row is genuinely empty

                        try:
                            product = get_object_or_404(Product, pk=product_id_str, business=business)
                            quantity = Decimal(submitted_quantities[i])
                            price = Decimal(submitted_prices[i])

                            if quantity <= 0 or price < 0:
                                messages.error(request, f"Invalid quantity or price for product {product.name}.")
                                raise ValueError("Invalid quantity or price for item")

                            new_sale_items_data.append({
                                'product': product,
                                'quantity': quantity,
                                'price': price,
                                'tax_type': product.tax_type,
                                'tax_rate': product.tax_rate,
                            })
                        except Product.DoesNotExist:
                            messages.error(request, f"Product with ID {product_id_str} not found.")
                            raise # Propagate to rollback transaction
                        except ValueError as e: # Catches Decimal conversion errors too
                            logger.error(f"Invalid data for item {product_id_str if product_id_str else 'unknown'}: {str(e)}")
                            messages.error(request, f"Invalid data for item {i+1} (Product ID: {product_id_str}). Ensure quantity and price are valid numbers.")
                            raise # Propagate to rollback transaction

                    # If we are here, all submitted item data is valid and products exist.
                    sale.items.all().delete() # Delete old items
                    for item_data_dict in new_sale_items_data:
                        SaleItem.objects.create(sale=sale, **item_data_dict)

                    # SaleItem.save() calls sale.calculate_totals().
                    # If new_sale_items_data is empty (e.g., all submitted rows were blank and skipped),
                    # this ensures totals are based on zero items.
                    if not new_sale_items_data:
                        sale.calculate_totals() # Explicitly calculate if all items were removed
                    # Otherwise, the last SaleItem.save() would have triggered it.
                    # To be safe, or if SaleItem might not always call it, an explicit call here is fine.
                    else:
                        # Ensure it's called once after all items are processed
                        sale.calculate_totals()

                else:
                    # No product data submitted (e.g., list was empty, or all pids were empty strings).
                    # This means items were not intended to be changed in this submission.
                    # Grand total and item-related fields should NOT be recalculated from scratch based on items.
                    # The existing grand_total on the sale object is preserved.
                    # sale.save() below will handle updating balance_due and payment_status
                    # using the PRESERVED grand_total and the NEW amount_paid.
                    pass # Explicitly do nothing with items or sale.calculate_totals()

                sale.updated_by = request.user
                sale.save() # This will use existing grand_total if items weren't touched, or new one if they were.
                            # It also updates balance_due and payment_status correctly.

                messages.success(request, 'Sale updated successfully!')
                return redirect('retail:sale_detail', sale_id=sale.id) # Corrected redirect argument

        except Exception as e:
            logger.error(f"Error updating sale {pk}: {str(e)}", exc_info=True)
            if not list(messages.get_messages(request)): # Check if specific messages were already added
                 messages.error(request, f'An unexpected error occurred while updating the sale: {str(e)}')

    context = {
        'sale': sale,
        'customers': customers,
        'products': products_for_dropdown, # Use the filtered list for the dropdown
        'payment_methods': payment_methods,
    }
    return render(request, 'retail/sale_edit.html', context)

