from django.shortcuts import render
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from business.models import Business
from retail.models import Product, Sale, SaleItem, Payment # Ensure Payment is imported
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

@login_required(login_url='userauths:retail_login')
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


# Note: Removed duplicate imports of transaction, JsonResponse, csrf_exempt, login_required, Decimal, json that were here.
# They are already imported at the top or just above this section.

@csrf_exempt
@login_required(login_url='userauths:retail_login')
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
                updated_by=request.user,
                payment_method=data.get('payment_method', 'cash'),
                # amount_paid is NOT set here directly. It's handled by Payment model.
                discount_amount=Decimal(data.get('discount_amount', 0))
            )
            sale.save() # Initial save to get sale ID

            for item_data in items:
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
                        tax_rate=Decimal(item_data.get('tax_rate', product.tax_rate)),
                        tax_type=item_data.get('tax_type', product.tax_type)
                    )
                    sale_item.save()

                    if product.manage_stock:
                        product.stock_quantity -= sale_item.quantity
                        product.save()
                except Product.DoesNotExist:
                    return JsonResponse(
                        {'success': False, 'message': f'Product ID {item_data.get("product_id")} not found'},
                        status=400
                    )
                except KeyError as e:
                    return JsonResponse(
                        {'success': False, 'message': f'Missing data in item: {str(e)}'},
                        status=400
                    )

            sale.calculate_totals() # This calls sale.save() internally

            amount_paid_from_request = Decimal(data.get('amount_paid', 0))
            if amount_paid_from_request > Decimal('0.00'):
                Payment.objects.create(
                    sale=sale,
                    amount=amount_paid_from_request,
                    payment_method=sale.payment_method,
                    created_by=request.user,
                    status='completed'
                )
            # Payment.save() updates sale.amount_paid and saves the sale.

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

from django.core.exceptions import ValidationError # Already imported but good to keep near its use if not at top

@login_required(login_url='userauths:retail_login')
def add_customer(request):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)
    try:
        business = request.user.profile.business
        # ... (rest of add_customer logic as it was, it seemed okay) ...
        if not business: # Ensure this check is here
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


@login_required(login_url='userauths:retail_login')
def customer_list(request):
    # Removed manual: if not request.user.is_authenticated:
    try:
        business = request.user.profile.business
        if not business:
             return JsonResponse({'error': 'User not associated with a business'}, status=400)
        # business_id = business.id # Not strictly needed if filtering on business object
    except AttributeError: # This can happen if user.profile doesn't exist
        return JsonResponse({'error': 'Business profile not found for user'}, status=400)
    except Business.DoesNotExist: # If user.profile.business is somehow None and accessed
        return JsonResponse({'error': 'Business not found for user profile'}, status=400)


    customers = Contact.objects.filter(
        business=business, # Filter by business object
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


from django.core.paginator import Paginator # Already imported but good to keep near use
from datetime import datetime # Already imported

@login_required(login_url='userauths:retail_login')
def sale_list(request):
    try:
        business = request.user.profile.business
    except AttributeError: # More specific exception for profile not existing
        messages.error(request, "User profile not found.")
        return redirect('userauths:retail_login') # Redirect to login if profile issue
    except Business.DoesNotExist: # More specific for business not existing on profile
        messages.error(request, "Business information not found for your profile.")
        return redirect('userauths:retail_login')

    sales_qs = Sale.objects.filter(business=business).select_related('customer').order_by('-date')
    # ... (rest of sale_list logic as it was) ...
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

@login_required(login_url='userauths:retail_login')
def sale_detail(request, sale_id):
    # Ensure business object is fetched safely
    try:
        business_bid = request.user.profile.business.bid
        business = get_object_or_404(Business, bid=business_bid)
    except AttributeError:
        messages.error(request, "User profile or business information is missing.")
        return redirect('userauths:retail_login')
    except Business.DoesNotExist:
        messages.error(request, "Business not found.")
        return redirect('userauths:retail_login')

    sale = get_object_or_404(Sale, id=sale_id, business=business)
    context = {
        'sale': sale,
        'business': business,
    }
    return render(request, 'retail/sale_detail.html', context)

@login_required(login_url='userauths:retail_login')
def print_receipt(request, sale_id):
    try:
        business_bid = request.user.profile.business.bid
        business = get_object_or_404(Business, bid=business_bid)
    except AttributeError:
        messages.error(request, "User profile or business information is missing.")
        return redirect('userauths:retail_login')
    except Business.DoesNotExist:
        messages.error(request, "Business not found.")
        return redirect('userauths:retail_login')

    sale = get_object_or_404(Sale, id=sale_id, business=business)
    context = {
        'sale': sale,
        'business': business,
    }
    return render(request, 'retail/receipt_print.html', context)


@login_required(login_url='userauths:retail_login')
def sale_edit(request, pk):
    try:
        business = request.user.profile.business
        if not business: # Explicit check if business is None after getattr
            raise Business.DoesNotExist
    except AttributeError:
        messages.error(request, "User profile not found.")
        return redirect('userauths:retail_login')
    except Business.DoesNotExist:
        messages.error(request, "Business information not found for your profile.")
        return redirect('userauths:retail_login')

    sale = get_object_or_404(Sale, pk=pk, business=business)
    current_total_paid_on_sale_load = sale.amount_paid # Capture amount paid at load time

    customers = Contact.objects.filter(business=business, type=Contact.ContactType.CUSTOMER, is_active=True)
    products_for_dropdown = Product.objects.filter(business=business, is_active=True)
    payment_methods = Sale.PAYMENT_METHODS

    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Update basic sale info from form
                # current_total_paid_on_sale_load is already defined outside POST check

                customer_id_str = request.POST.get('customer')
                if customer_id_str:
                    sale.customer = get_object_or_404(Contact, pk=customer_id_str, business=business, type=Contact.ContactType.CUSTOMER)
                else:
                    sale.customer = None

                sale.date = request.POST.get('date') # Consider timezone conversion if needed
                sale.payment_method = request.POST.get('payment_method', sale.payment_method)
                sale.discount_percent = Decimal(request.POST.get('discount', 0))

                # Removed direct assignment: sale.amount_paid = Decimal(request.POST.get('amount_paid', 0))
                new_total_amount_paid_from_form = Decimal(request.POST.get('amount_paid', 0))

                # Item processing (this might call sale.calculate_totals() which calls sale.save())
                submitted_products_ids = request.POST.getlist('product')
                if submitted_products_ids and any(pid for pid in submitted_products_ids if pid.strip()):
                    # ... (existing item processing logic) ...
                    new_sale_items_data = []
                    submitted_prices = request.POST.getlist('price')
                    submitted_quantities = request.POST.getlist('quantity')

                    if not (len(submitted_products_ids) == len(submitted_prices) == len(submitted_quantities)):
                        messages.error(request, "Mismatch in submitted item data counts. Please check items.")
                        raise ValueError("Item data lists length mismatch")

                    for i, product_id_str in enumerate(submitted_products_ids):
                        if not product_id_str.strip():
                            if submitted_prices[i].strip() or submitted_quantities[i].strip():
                                messages.error(request, f"Missing product for item {i+1} but other data present.")
                                raise ValueError(f"Missing product for item {i+1}")
                            continue

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
                            raise
                        except ValueError as e:
                            logger.error(f"Invalid data for item {product_id_str if product_id_str else 'unknown'}: {str(e)}")
                            messages.error(request, f"Invalid data for item {i+1} (Product ID: {product_id_str}). Ensure quantity and price are valid numbers.")
                            raise

                    sale.items.all().delete()
                    for item_data_dict in new_sale_items_data:
                        SaleItem.objects.create(sale=sale, **item_data_dict)

                    if not new_sale_items_data: # if all items removed
                        sale.calculate_totals()
                    else: # if items were changed/added
                        sale.calculate_totals() # This calls sale.save()
                else:
                    # No items submitted for change, but discount might have changed.
                    # If discount_percent changed, totals need recalculation.
                    # Sale.calculate_totals() also handles discount_percent.
                    # Check if discount actually changed to avoid unnecessary save if only amount_paid changed.
                    if sale.discount_percent != Decimal(request.POST.get('discount', 0)): # Compare with form value
                         sale.calculate_totals() # This will save the sale with old amount_paid if no items changed.

                # Payment processing after item changes and potential calculate_totals()
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
                        # Payment.save() updates sale.amount_paid and saves the sale.
                        # sale object in memory here might be stale regarding amount_paid
                        # but the final sale.save() below will use the DB value if not explicitly set on instance.

                sale.updated_by = request.user
                # Final save to ensure all changes (including updated amount_paid from Payment.save)
                # are reflected and payment_status is correctly set.
                # If Payment.save() already saved the sale, this save updates it further if other fields changed.
                sale.save()

                messages.success(request, 'Sale updated successfully!')
                return redirect('retail:sale_detail', sale_id=sale.id)

        except Exception as e:
            logger.error(f"Error updating sale {pk}: {str(e)}", exc_info=True)
            if not list(messages.get_messages(request)):
                 messages.error(request, f'An unexpected error occurred while updating the sale: {str(e)}')

    context = {
        'sale': sale,
        'customers': customers,
        'products': products_for_dropdown,
        'payment_methods': payment_methods,
    }
    return render(request, 'retail/sale_edit.html', context)
