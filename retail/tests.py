import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model # Import get_user_model
from business.models import Business
from userauths.models import UserProfile
from retail.models import Product, Sale, SaleItem, Payment, Contact, Category, Unit

User = get_user_model() # Use get_user_model to get the active User model

class ProcessSaleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.business = Business.objects.create(name="Test Business", bid="TBUSINESS") # Added unique bid
        self.user = User.objects.create_user(username='testuser', password='password123', email='testuser@example.com') # Added email
        # Ensure Profile is created; if signals are not reliable in tests, create explicitly
        if not hasattr(self.user, 'profile') or self.user.profile is None: # Check if profile is None
            self.profile = UserProfile.objects.create(user=self.user, business=self.business, user_type='staff')
        else:
            self.user.profile.business = self.business
            self.user.profile.user_type = 'staff' # Ensure user_type is appropriate if business is linked
            self.user.profile.save()
            self.profile = self.user.profile

        self.client.login(username='testuser', password='password123')

        self.category = Category.objects.create(name="Test Category", business=self.business)
        self.unit = Unit.objects.create(name="Piece", abbreviation="pc", business=self.business)

        self.product1 = Product.objects.create(
            name="Test Product 1",
            business=self.business,
            category=self.category,
            unit=self.unit,
            price=Decimal("100.00"),
            tax_rate=Decimal("10.00"),
            manage_stock=False,
            created_by=self.user # Added created_by
        )
        self.product2 = Product.objects.create(
            name="Test Product 2",
            business=self.business,
            category=self.category,
            unit=self.unit,
            price=Decimal("50.00"),
            tax_rate=Decimal("5.00"),
            manage_stock=False,
            created_by=self.user # Added created_by
        )
        self.customer = Contact.objects.create(
            first_name="Test",
            last_name="Customer",
            business=self.business,
            type=Contact.ContactType.CUSTOMER,
            created_by=self.user # Added created_by
        )
        try:
            self.process_sale_url = reverse('retail:process_sale')
        except NoReverseMatch:
            # Fallback if retail namespace isn't defined, try without it
            # This can happen if urls.py is not set up with app_name = 'retail'
            # or if the main project urls.py does not include retail.urls with a namespace
            self.process_sale_url = reverse('process_sale')


    def _prepare_sale_data(self, items_data, amount_paid, discount_amount="0.00", customer_id=None, payment_method="cash"):
        return {
            "items": items_data,
            "customer_id": str(customer_id if customer_id else self.customer.id), # Ensure customer_id is string
            "payment_method": payment_method,
            "amount_paid": str(amount_paid),
            "discount_amount": str(discount_amount),
        }

    def test_process_sale_full_payment(self):
        items_data = [
            {"product_id": self.product1.id, "quantity": "1", "price": "100.00", "tax_rate": "10.00", "tax_type": "standard"},
            {"product_id": self.product2.id, "quantity": "2", "price": "50.00", "tax_rate": "5.00", "tax_type": "standard"}
        ]
        # Product1: 1 * 100 = 100. Tax: 100 * 0.10 = 10.
        # Product2: 2 * 50 = 100. Tax: 100 * 0.05 = 5.
        # Sale Subtotal (sum of item subtotals pre-tax): 100 + 100 = 200
        # Sale Tax Amount (sum of item taxes): 10 + 5 = 15
        # Sale Grand Total: 200 + 15 = 215
        grand_total_expected = Decimal("215.00")
        amount_to_pay = grand_total_expected

        payload = self._prepare_sale_data(items_data, amount_to_pay)

        response = self.client.post(
            self.process_sale_url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, 200, response_data) # Show response data on failure
        self.assertTrue(response_data['success'])

        sale = Sale.objects.get(invoice_number=response_data['invoice_number'])

        # Verify Payment first to ensure it was created correctly
        payments = Payment.objects.filter(sale=sale)
        self.assertEqual(payments.count(), 1)
        payment = payments.first()
        self.assertEqual(payment.amount, amount_to_pay)
        self.assertEqual(payment.payment_method, payload['payment_method'])
        self.assertEqual(payment.status, 'completed')

        # Now verify Sale details
        self.assertEqual(sale.subtotal, Decimal("200.00"))
        self.assertEqual(sale.tax_amount, Decimal("15.00"))
        self.assertEqual(sale.grand_total, grand_total_expected)
        self.assertEqual(sale.amount_paid, amount_to_pay) # This was the failing line
        self.assertEqual(sale.payment_status, 'paid')
        self.assertEqual(sale.balance_due, Decimal("0.00"))


    def test_process_sale_partial_payment(self):
        items_data = [
            {"product_id": self.product1.id, "quantity": "1", "price": "100.00", "tax_rate": "10.00", "tax_type": "standard"}
        ]
        # Product1: 1 * 100 = 100. Tax: 100 * 0.10 = 10.
        # Sale Subtotal: 100
        # Sale Tax Amount: 10
        # Sale Grand Total: 110
        grand_total_expected = Decimal("110.00")
        amount_to_pay = Decimal("50.00")

        payload = self._prepare_sale_data(items_data, amount_to_pay)

        response = self.client.post(
            self.process_sale_url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, 200, response_data)
        self.assertTrue(response_data['success'])

        sale = Sale.objects.get(invoice_number=response_data['invoice_number'])

        self.assertEqual(sale.grand_total, grand_total_expected)
        self.assertEqual(sale.amount_paid, amount_to_pay)
        self.assertEqual(sale.payment_status, 'partial')
        self.assertEqual(sale.balance_due, grand_total_expected - amount_to_pay)

        payments = Payment.objects.filter(sale=sale)
        self.assertEqual(payments.count(), 1)
        payment = payments.first()
        self.assertEqual(payment.amount, amount_to_pay)

    def test_process_sale_no_initial_payment(self):
        items_data = [
            {"product_id": self.product1.id, "quantity": "1", "price": "100.00", "tax_rate": "10.00", "tax_type": "standard"}
        ]
        grand_total_expected = Decimal("110.00") # 100 + 10 tax
        amount_to_pay = Decimal("0.00")

        payload = self._prepare_sale_data(items_data, amount_to_pay)

        response = self.client.post(
            self.process_sale_url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, 200, response_data)
        self.assertTrue(response_data['success'])

        sale = Sale.objects.get(invoice_number=response_data['invoice_number'])

        self.assertEqual(sale.grand_total, grand_total_expected)
        self.assertEqual(sale.amount_paid, Decimal("0.00"))
        self.assertEqual(sale.payment_status, 'unpaid')
        self.assertEqual(sale.balance_due, grand_total_expected)

        payments = Payment.objects.filter(sale=sale)
        self.assertEqual(payments.count(), 0)

    def test_process_sale_with_fixed_discount_full_payment(self):
        items_data = [
            {"product_id": self.product1.id, "quantity": "2", "price": "100.00", "tax_rate": "10.00", "tax_type": "standard"}
        ]
        # Sale Subtotal (sum of item.price * item.quantity): 2 * 100 = 200
        # Sale Tax Amount (sum of item_subtotal * item_tax_rate): (2 * 100) * 0.10 = 20
        # Discount Amount (fixed): 20
        # Sale Grand Total: Subtotal - DiscountAmount + TaxAmount = 200 - 20 + 20 = 200
        grand_total_expected = Decimal("200.00")
        discount_amount = Decimal("20.00")
        amount_to_pay = grand_total_expected

        payload = self._prepare_sale_data(items_data, amount_to_pay, discount_amount=discount_amount)

        response = self.client.post(
            self.process_sale_url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, 200, response_data)
        self.assertTrue(response_data['success'])

        sale = Sale.objects.get(invoice_number=response_data['invoice_number'])

        self.assertEqual(sale.subtotal, Decimal("200.00"))
        self.assertEqual(sale.discount_amount, discount_amount)
        self.assertEqual(sale.tax_amount, Decimal("20.00"))
        self.assertEqual(sale.grand_total, grand_total_expected)
        self.assertEqual(sale.amount_paid, amount_to_pay)
        self.assertEqual(sale.payment_status, 'paid')
        self.assertEqual(sale.balance_due, Decimal("0.00"))

        payments = Payment.objects.filter(sale=sale)
        self.assertEqual(payments.count(), 1)
        payment = payments.first()
        self.assertEqual(payment.amount, amount_to_pay)

    def test_process_sale_item_data_uses_product_tax_rate_if_not_provided(self):
        # Product1 has tax_rate 10%
        items_data = [
            {"product_id": self.product1.id, "quantity": "1", "price": "100.00", "tax_type": "standard"},
        ]
        # Subtotal = 100
        # Tax from product1.tax_rate = 100 * 0.10 = 10
        # Grand Total = 100 + 10 = 110
        grand_total_expected = Decimal("110.00")
        amount_to_pay = grand_total_expected

        payload = self._prepare_sale_data(items_data, amount_to_pay)

        response = self.client.post(
            self.process_sale_url,
            data=json.dumps(payload),
            content_type='application/json'
        )

        response_data = response.json()
        self.assertEqual(response.status_code, 200, response_data)
        self.assertTrue(response_data['success'])

        sale = Sale.objects.get(invoice_number=response_data['invoice_number'])
        self.assertEqual(sale.grand_total, grand_total_expected)

        sale_item = SaleItem.objects.get(sale=sale, product=self.product1)
        self.assertEqual(sale_item.tax_rate, self.product1.tax_rate)
        self.assertEqual(sale.tax_amount, (sale_item.price * sale_item.quantity) * (self.product1.tax_rate / Decimal(100)))


    def test_process_sale_invalid_customer(self):
        items_data = [{"product_id": self.product1.id, "quantity": "1", "price": "100.00", "tax_type": "standard"}]
        payload = self._prepare_sale_data(items_data, "110.00", customer_id=99999) # Non-existent customer

        response = self.client.post(
            self.process_sale_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, 400, response_data)
        self.assertFalse(response_data['success'])
        self.assertIn('Customer not found', response_data['message'])

    def test_process_sale_no_items(self):
        items_data = []
        payload = self._prepare_sale_data(items_data, "0.00")

        response = self.client.post(
            self.process_sale_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, 400, response_data)
        self.assertFalse(response_data['success'])
        self.assertIn('No items provided', response_data['message'])

    def test_process_sale_invalid_product(self):
        items_data = [{"product_id": 99999, "quantity": "1", "price": "100.00", "tax_type": "standard"}]
        payload = self._prepare_sale_data(items_data, "100.00")

        response = self.client.post(
            self.process_sale_url,
            data=json.dumps(payload),
            content_type='application/json'
        )
        response_data = response.json()
        self.assertEqual(response.status_code, 400, response_data)
        self.assertFalse(response_data['success'])
        self.assertIn('Product ID 99999 not found', response_data['message'])

    def test_process_sale_missing_item_data_fields(self):
        # Missing 'price'
        items_data = [{"product_id": self.product1.id, "quantity": "1"}]
        payload = self._prepare_sale_data(items_data, "10.00")
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code, 400, response_data)
        self.assertFalse(response_data['success'])
        self.assertIn('Missing data in item', response_data['message'])

        # Missing 'quantity'
        items_data = [{"product_id": self.product1.id, "price": "100.00"}]
        payload = self._prepare_sale_data(items_data, "10.00")
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code, 400, response_data)
        self.assertFalse(response_data['success'])
        self.assertIn('Missing data in item', response_data['message'])
