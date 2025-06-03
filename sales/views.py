from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Business, Contact, Product, Order, OrderItem, Payment
import json
from decimal import Decimal
import logging
from django.core.paginator import Paginator

logger = logging.getLogger(__name__)

def dashboard(request):
    return render(request, 'sales/dashboard_sales.html')


def sales_view(request):
    """Render the sales page with businesses, products, and pre-selected Walk-in Customer."""
    businesses = Business.objects.all()
    business_id = request.GET.get("business_id")

    customers = []
    default_customer = None

    if business_id:
        business = Business.objects.get(id=business_id)
        customers = Contact.objects.filter(business=business, type="customer")  # Filter customers by business

        # Fetch Walk-in Customer for the selected business
        default_customer = Contact.objects.filter(
            business=business,
            first_name="Walk-in",
            last_name="Customer"
        ).first()

    products = Product.objects.all()

    return render(request, "sales/sales.html", {
        "businesses": businesses,
        "customers": customers,
        "products": products,
        "default_customer": default_customer
    })


from django.http import JsonResponse
from .models import Contact

@csrf_exempt
def customer_search(request):
    """AJAX endpoint to fetch customers dynamically based on business ID with pagination."""
    try:
        # Get query parameters
        business_id = request.GET.get('business_id')
        q = request.GET.get('q', '').strip()  # Search term
        page = int(request.GET.get('page', 1))  # Page number for pagination
        page_size = 10  # Number of customers per page

        # Validate business_id
        if not business_id:
            return JsonResponse({"error": "Missing business_id"}, status=400)

        # Fetch customers for the selected business
        customers = Contact.objects.filter(type="customer", business_id=business_id)

        # Apply search filter if a search term is provided
        if q:
            customers = customers.filter(first_name__icontains=q)

        # Paginate the results
        paginator = Paginator(customers, page_size)
        page_customers = paginator.page(page)

        # Prepare the response data
        results = [
            {
                "id": customer.id,
                "text": f"{customer.first_name} {customer.last_name}"  # Required by Select2
            }
            for customer in page_customers
        ]

        # Return the response with pagination info
        return JsonResponse({
            "results": results,
            "pagination": {
                "more": page_customers.has_next()  # Indicates if there are more results
            }
        })

    except Exception as e:
        # Log the error and return a 500 response
        print("❌ Error in customer_search:", str(e))  # Debugging
        return JsonResponse({"error": str(e)}, status=500)


@csrf_exempt
def product_search(request):
    # Get query parameters
    business_id = request.GET.get('business_id')
    search_term = request.GET.get('q', '')  # Search term from Select2
    page = int(request.GET.get('page', 1))  # Page number for pagination
    page_size = 10  # Number of products per page

    # Fetch products for the selected business and filter by search term
    products = Product.objects.filter(business_id=business_id, name__icontains=search_term)

    # Paginate the results
    paginator = Paginator(products, page_size)
    page_products = paginator.page(page)

    # Prepare the response data
    results = [
        {
            "id": product.id,
            "text": product.name,  # Required by Select2
            "sku": product.sku,
            "price": product.price
        }
        for product in page_products
    ]

    # Return the response with pagination info
    return JsonResponse({
        "results": results,
        "pagination": {
            "more": page_products.has_next()  # Indicates if there are more results
        }
    })

@csrf_exempt
def get_product_details(request):
    """AJAX endpoint to fetch product details (price) when selected."""
    try:
        if request.method == "POST":
            data = json.loads(request.body)
            product_id = data.get("product_id")

            product = get_object_or_404(Product, id=product_id)
            return JsonResponse({"price": str(product.price)})

        return JsonResponse({"error": "Invalid request"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from .models import Order, OrderItem, Contact

logger = logging.getLogger(__name__)

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
import logging
from decimal import Decimal
from .models import Order, OrderItem, Contact

logger = logging.getLogger(__name__)

@csrf_exempt
def create_order(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            business_id = data.get('business_id')
            customer_id = data.get('customer_id')
            shipping_cost = Decimal(data.get('shipping_cost', 0))
            order_discount = Decimal(data.get('order_discount', 0))
            total_amount = Decimal(data.get('total_amount', 0))
            paid_amount = Decimal(data.get('paid_amount', 0))  # New field
            due_amount = Decimal(data.get('due_amount', 0))  # New field
            products = data.get('products', [])

            # Log the received customer_id for debugging
            logger.info(f"Received customer_id: {customer_id}")

            # Fetch the Walk-in Customer only if no customer is selected
            if not customer_id:
                logger.info("No customer selected. Fetching Walk-in Customer.")
                walk_in_customer = Contact.objects.filter(business_id=business_id, is_walk_in=True).first()
                if not walk_in_customer:
                    logger.error("No Walk-in Customer found for this business.")
                    return JsonResponse({'error': 'No Walk-in Customer found for this business.'}, status=400)
                customer_id = walk_in_customer.id
                logger.info(f"Using Walk-in Customer ID: {customer_id}")

            # Log the final customer_id being used
            logger.info(f"Final customer_id for order: {customer_id}")

            # Create and save the Order instance
            with transaction.atomic():
                order = Order(
                    business_id=business_id,
                    customer_id=customer_id,
                    shipping_cost=shipping_cost,
                    discount=order_discount,
                    total_amount=total_amount,
                    paid_amount=paid_amount,  # New field
                    due_amount=due_amount,  # New field
                )
                order.save()

                # Add order items
                for product in products:
                    OrderItem.objects.create(
                        order=order,
                        product_id=product['product_id'],
                        quantity=product['quantity'],
                        item_discount=Decimal(product['item_discount']),
                        total_price=Decimal(product['total_price']),
                    )

            return JsonResponse({'order_id': order.id, 'message': 'Order created successfully'}, status=201)

        except Exception as e:
            logger.error(f"Error creating order: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def edit_order(request, order_id):
    """Render the sales edit page with the order details."""
    order = get_object_or_404(Order, id=order_id)
    businesses = Business.objects.all()
    products = Product.objects.all()

    return render(request, "sales/sales_edit.html", {
        "order": order,
        "businesses": businesses,
        "products": products,
    })


@csrf_exempt
def update_order(request, order_id):
    if request.method == 'PUT':
        try:
            data = json.loads(request.body)
            business_id = data.get('business_id')
            customer_id = data.get('customer_id')
            shipping_cost = Decimal(data.get('shipping_cost', 0))
            order_discount = Decimal(data.get('order_discount', 0))
            total_amount = Decimal(data.get('total_amount', 0))
            paid_amount = Decimal(data.get('paid_amount', 0))  # Total paid amount
            due_amount = Decimal(data.get('due_amount', 0))  # Remaining due amount
            products = data.get('products', [])
            payments = data.get('payments', [])  # List of new payments

            # Log the received customer_id for debugging
            logger.info(f"Received customer_id: {customer_id}")

            # Fetch the Walk-in Customer only if no customer is selected
            if not customer_id:
                logger.info("No customer selected. Fetching Walk-in Customer.")
                walk_in_customer = Contact.objects.filter(business_id=business_id, is_walk_in=True).first()
                if not walk_in_customer:
                    logger.error("No Walk-in Customer found for this business.")
                    return JsonResponse({'error': 'No Walk-in Customer found for this business.'}, status=400)
                customer_id = walk_in_customer.id
                logger.info(f"Using Walk-in Customer ID: {customer_id}")

            # Log the final customer_id being used
            logger.info(f"Final customer_id for order: {customer_id}")

            # Fetch the existing order
            order = Order.objects.get(id=order_id)

            # Update the order fields
            with transaction.atomic():
                order.business_id = business_id
                order.customer_id = customer_id
                order.shipping_cost = shipping_cost
                order.discount = order_discount
                order.total_amount = total_amount
                order.paid_amount = paid_amount
                order.due_amount = due_amount

                # Update payment status
                if paid_amount >= total_amount:
                    order.payment_status = 'Paid'
                elif paid_amount > 0:
                    order.payment_status = 'Partially Paid'
                else:
                    order.payment_status = 'Pending'

                order.save()

                # Delete existing order items
                OrderItem.objects.filter(order=order).delete()

                # Add updated order items
                for product in products:
                    OrderItem.objects.create(
                        order=order,
                        product_id=product['product_id'],
                        quantity=product['quantity'],
                        item_discount=Decimal(product['item_discount']),
                        total_price=Decimal(product['total_price']),
                    )

                # Delete existing payments (optional, if you want to replace all payments)
                Payment.objects.filter(order=order).delete()

                # Add new payments
                for payment in payments:
                    Payment.objects.create(
                        order=order,
                        amount=Decimal(payment['amount']),
                        payment_method=payment['method'],
                        notes=payment['notes']
                    )

            return JsonResponse({'order_id': order.id, 'message': 'Order updated successfully'}, status=200)

        except Order.DoesNotExist:
            logger.error(f"Order with ID {order_id} not found.")
            return JsonResponse({'error': 'Order not found.'}, status=404)
        except Exception as e:
            logger.error(f"Error updating order: {str(e)}")
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


def sales_list(request):
    """Display the list of sales transactions."""
    orders = Order.objects.all().order_by("-id")
    return render(request, "sales/sales_list.html", {"orders": orders})