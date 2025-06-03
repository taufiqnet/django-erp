import json
from decimal import Decimal
from django.utils import timezone # Added for date
from django.test import TestCase, Client
from django.urls import reverse, NoReverseMatch
from django.contrib.auth import get_user_model
from business.models import Business
from userauths.models import UserProfile
from retail.models import Product, Sale, SaleItem, Payment, Contact, Category, Unit

User = get_user_model()

class ProcessSaleTests(TestCase): # Existing tests ...
    def setUp(self):
        self.client = Client()
        self.business = Business.objects.create(name="Test Business", bid="TBUSINESS")
        self.user = User.objects.create_user(username='testuser', password='password123', email='testuser@example.com')
        if not hasattr(self.user, 'profile') or self.user.profile is None:
            self.profile = UserProfile.objects.create(user=self.user, business=self.business, user_type='staff')
        else:
            self.user.profile.business = self.business
            self.user.profile.user_type = 'staff'
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
            created_by=self.user
        )
        self.product2 = Product.objects.create(
            name="Test Product 2",
            business=self.business,
            category=self.category,
            unit=self.unit,
            price=Decimal("50.00"),
            tax_rate=Decimal("5.00"),
            manage_stock=False,
            created_by=self.user
        )
        self.customer = Contact.objects.create(
            first_name="Test",
            last_name="Customer",
            business=self.business,
            type=Contact.ContactType.CUSTOMER,
            created_by=self.user
        )
        try:
            self.process_sale_url = reverse('retail:process_sale')
        except NoReverseMatch:
            self.process_sale_url = reverse('process_sale')


    def _prepare_sale_data(self, items_data, amount_paid, discount_amount="0.00", customer_id=None, payment_method="cash"):
        return {
            "items": items_data,
            "customer_id": str(customer_id if customer_id else self.customer.id),
            "payment_method": payment_method,
            "amount_paid": str(amount_paid),
            "discount_amount": str(discount_amount),
        }

    def test_process_sale_full_payment(self):
        items_data = [
            {"product_id": self.product1.id, "quantity": "1", "price": "100.00", "tax_rate": "10.00", "tax_type": "standard"},
            {"product_id": self.product2.id, "quantity": "2", "price": "50.00", "tax_rate": "5.00", "tax_type": "standard"}
        ]
        grand_total_expected = Decimal("215.00")
        amount_to_pay = grand_total_expected
        payload = self._prepare_sale_data(items_data, amount_to_pay)
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code, 200, response_data)
        self.assertTrue(response_data['success'])
        sale = Sale.objects.get(invoice_number=response_data['invoice_number'])
        payments = Payment.objects.filter(sale=sale)
        self.assertEqual(payments.count(), 1)
        payment = payments.first()
        self.assertEqual(payment.amount, amount_to_pay)
        self.assertEqual(payment.payment_method, payload['payment_method'])
        self.assertEqual(payment.status, 'completed')
        self.assertEqual(sale.subtotal, Decimal("200.00"))
        self.assertEqual(sale.tax_amount, Decimal("15.00"))
        self.assertEqual(sale.grand_total, grand_total_expected)
        self.assertEqual(sale.amount_paid, amount_to_pay)
        self.assertEqual(sale.payment_status, 'paid')
        self.assertEqual(sale.balance_due, Decimal("0.00"))

    def test_process_sale_partial_payment(self):
        items_data = [{"product_id": self.product1.id, "quantity": "1", "price": "100.00", "tax_rate": "10.00", "tax_type": "standard"}]
        grand_total_expected = Decimal("110.00")
        amount_to_pay = Decimal("50.00")
        payload = self._prepare_sale_data(items_data, amount_to_pay)
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
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
        items_data = [{"product_id": self.product1.id, "quantity": "1", "price": "100.00", "tax_rate": "10.00", "tax_type": "standard"}]
        grand_total_expected = Decimal("110.00")
        amount_to_pay = Decimal("0.00")
        payload = self._prepare_sale_data(items_data, amount_to_pay)
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
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
        items_data = [{"product_id": self.product1.id, "quantity": "2", "price": "100.00", "tax_rate": "10.00", "tax_type": "standard"}]
        grand_total_expected = Decimal("200.00")
        discount_amount = Decimal("20.00")
        amount_to_pay = grand_total_expected
        payload = self._prepare_sale_data(items_data, amount_to_pay, discount_amount=discount_amount)
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
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
        items_data = [{"product_id": self.product1.id, "quantity": "1", "price": "100.00", "tax_type": "standard"}]
        grand_total_expected = Decimal("110.00")
        amount_to_pay = grand_total_expected
        payload = self._prepare_sale_data(items_data, amount_to_pay)
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
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
        payload = self._prepare_sale_data(items_data, "110.00", customer_id=99999)
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code, 400, response_data)
        self.assertFalse(response_data['success'])
        self.assertIn('Customer not found', response_data['message'])

    def test_process_sale_no_items(self):
        items_data = []
        payload = self._prepare_sale_data(items_data, "0.00")
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code, 400, response_data)
        self.assertFalse(response_data['success'])
        self.assertIn('No items provided', response_data['message'])

    def test_process_sale_invalid_product(self):
        items_data = [{"product_id": 99999, "quantity": "1", "price": "100.00", "tax_type": "standard"}]
        payload = self._prepare_sale_data(items_data, "100.00")
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code, 400, response_data)
        self.assertFalse(response_data['success'])
        self.assertIn('Product ID 99999 not found', response_data['message'])

    def test_process_sale_missing_item_data_fields(self):
        items_data = [{"product_id": self.product1.id, "quantity": "1"}]
        payload = self._prepare_sale_data(items_data, "10.00")
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code, 400, response_data)
        self.assertFalse(response_data['success'])
        self.assertIn('Missing data in item', response_data['message'])
        items_data = [{"product_id": self.product1.id, "price": "100.00"}]
        payload = self._prepare_sale_data(items_data, "10.00")
        response = self.client.post(self.process_sale_url, data=json.dumps(payload), content_type='application/json')
        response_data = response.json()
        self.assertEqual(response.status_code, 400, response_data)
        self.assertFalse(response_data['success'])
        self.assertIn('Missing data in item', response_data['message'])


class EditSaleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.business = Business.objects.create(name="Edit Test Business", bid="ETBUS")
        self.user = User.objects.create_user(username='edittestuser', password='password123', email='edit_testuser@example.com')

        if not hasattr(self.user, 'profile') or self.user.profile is None:
            self.profile = UserProfile.objects.create(user=self.user, business=self.business, user_type='staff')
        else:
            self.user.profile.business = self.business
            self.user.profile.user_type = 'staff'
            self.user.profile.save()
            self.profile = self.user.profile

        self.client.login(username='edittestuser', password='password123')

        self.category = Category.objects.create(name="Edit Category", business=self.business)
        self.unit = Unit.objects.create(name="Box", abbreviation="box", business=self.business)

        self.product1 = Product.objects.create(
            name="Editable Product 1", business=self.business, category=self.category, unit=self.unit,
            price=Decimal("200.00"), tax_rate=Decimal("5.00"), manage_stock=False, created_by=self.user
        )
        self.product2 = Product.objects.create(
            name="Editable Product 2", business=self.business, category=self.category, unit=self.unit,
            price=Decimal("30.00"), tax_rate=Decimal("5.00"), manage_stock=False, created_by=self.user
        )
        self.customer = Contact.objects.create(
            first_name="Edit Test", last_name="Customer", business=self.business,
            type=Contact.ContactType.CUSTOMER, created_by=self.user
        )

    def _create_initial_sale(self, items_config, initial_payment_amount=Decimal("0.00"), customer=None, payment_method='cash', discount_percent=Decimal("0.00")):
        sale = Sale.objects.create(
            business=self.business,
            customer=customer if customer else self.customer,
            created_by=self.user,
            updated_by=self.user,
            payment_method=payment_method,
            discount_percent=discount_percent
            # amount_paid is NOT set here directly; it comes from Payment objects
        )
        for item_conf in items_config:
            SaleItem.objects.create(
                sale=sale, product=item_conf['product'], quantity=item_conf['quantity'],
                price=item_conf['price'], tax_rate=item_conf['product'].tax_rate, tax_type=item_conf['product'].tax_type
            )
        sale.calculate_totals() # This also calls sale.save()

        if initial_payment_amount > Decimal("0.00"):
            Payment.objects.create(
                sale=sale, amount=initial_payment_amount, payment_method=payment_method,
                created_by=self.user, status='completed'
            )
            # Payment.save() updates sale.amount_paid and saves sale again.
            sale.refresh_from_db() # Ensure sale object in test has the latest amount_paid
        return sale

    def _prepare_edit_sale_post_data(self, sale, items_post_data, amount_paid_form, discount_percent_form=None, payment_method_form=None):
        data = {
            'customer': str(sale.customer.id) if sale.customer else "",
            'date': sale.date.strftime('%Y-%m-%d %H:%M:%S'), # Format date as string
            'payment_method': payment_method_form if payment_method_form else sale.payment_method,
            'discount': str(discount_percent_form if discount_percent_form is not None else sale.discount_percent),
            'amount_paid': str(amount_paid_form),
            'product': [str(item['product_id']) for item in items_post_data],
            'quantity': [str(item['quantity']) for item in items_post_data],
            'price': [str(item['price']) for item in items_post_data],
            # tax_rate and tax_type for items are taken from product defaults in the view if not provided
        }
        return data

    def test_edit_partially_paid_sale_to_full_payment(self):
        items_config = [{'product': self.product1, 'quantity': Decimal("1"), 'price': self.product1.price}] # P1: 200, Tax: 10 => GT: 210
        initial_sale = self._create_initial_sale(items_config, initial_payment_amount=Decimal("100.00"))
        self.assertEqual(initial_sale.amount_paid, Decimal("100.00"))
        self.assertEqual(initial_sale.payment_status, 'partial')
        initial_payment_count = Payment.objects.filter(sale=initial_sale).count() # Should be 1

        grand_total_expected = initial_sale.grand_total # Should be 210

        # Prepare POST data for editing - keeping items the same, changing amount_paid
        items_post_data = [{'product_id': self.product1.id, 'quantity': "1", 'price': self.product1.price}]
        form_amount_paid = grand_total_expected # Pay in full: 210

        edit_url = reverse('retail:sale_edit', kwargs={'pk': initial_sale.pk})
        response = self.client.post(edit_url, data=self._prepare_edit_sale_post_data(initial_sale, items_post_data, form_amount_paid))

        self.assertEqual(response.status_code, 302, response.content) # Expect redirect

        updated_sale = Sale.objects.get(pk=initial_sale.pk)
        self.assertEqual(Payment.objects.filter(sale=updated_sale).count(), initial_payment_count + 1)

        latest_payment = Payment.objects.filter(sale=updated_sale).latest('created_at')
        self.assertEqual(latest_payment.amount, form_amount_paid - Decimal("100.00")) # Additional payment: 210 - 100 = 110

        self.assertEqual(updated_sale.amount_paid, grand_total_expected)
        self.assertEqual(updated_sale.payment_status, 'paid')
        self.assertEqual(updated_sale.balance_due, Decimal("0.00"))

    def test_edit_sale_items_and_pay_full_amount(self):
        items_config = [{'product': self.product1, 'quantity': Decimal("1"), 'price': self.product1.price}] # P1: 200, Tax: 10 => GT: 210
        initial_sale = self._create_initial_sale(items_config, initial_payment_amount=Decimal("0.00")) # Initially unpaid
        self.assertEqual(initial_sale.payment_status, 'unpaid')
        initial_payment_count = Payment.objects.filter(sale=initial_sale).count() # Should be 0

        # New items for POST data: P1 x 1 (200), P2 x 2 (60) => Subtotal: 260. Tax: (200*0.05=10) + (60*0.05=3) = 13. GT = 273
        items_post_data = [
            {'product_id': self.product1.id, 'quantity': "1", 'price': self.product1.price},
            {'product_id': self.product2.id, 'quantity': "2", 'price': self.product2.price}
        ]
        new_grand_total_expected = Decimal("200") * (1 + self.product1.tax_rate/100) + \
                                 Decimal("60") * (1 + self.product2.tax_rate/100)
        new_grand_total_expected = Decimal("210") + Decimal("63") # P1(200+10 tax) + P2(60+3 tax) = 273

        form_amount_paid = new_grand_total_expected # Pay new full amount: 273

        edit_url = reverse('retail:sale_edit', kwargs={'pk': initial_sale.pk})
        response = self.client.post(edit_url, data=self._prepare_edit_sale_post_data(initial_sale, items_post_data, form_amount_paid))

        self.assertEqual(response.status_code, 302, response.content)

        updated_sale = Sale.objects.get(pk=initial_sale.pk)
        # Calculate expected grand total based on items_post_data
        expected_subtotal = self.product1.price * 1 + self.product2.price * 2 # 200 + 60 = 260
        expected_tax = (self.product1.price * 1 * (self.product1.tax_rate/100)) + \
                       (self.product2.price * 2 * (self.product2.tax_rate/100)) # 10 + 3 = 13
        expected_grand_total_calc = expected_subtotal + expected_tax # 260 + 13 = 273

        self.assertEqual(updated_sale.grand_total, expected_grand_total_calc)
        self.assertEqual(Payment.objects.filter(sale=updated_sale).count(), initial_payment_count + 1) # New payment created

        latest_payment = Payment.objects.filter(sale=updated_sale).latest('created_at')
        self.assertEqual(latest_payment.amount, form_amount_paid) # Payment is for the full new amount

        self.assertEqual(updated_sale.amount_paid, form_amount_paid)
        self.assertEqual(updated_sale.payment_status, 'paid')

    def test_edit_sale_increase_payment_still_partial(self):
        items_config = [{'product': self.product1, 'quantity': Decimal("2"), 'price': self.product1.price}] # P1x2: 400, Tax: 20 => GT: 420
        initial_sale = self._create_initial_sale(items_config, initial_payment_amount=Decimal("100.00"))
        self.assertEqual(initial_sale.amount_paid, Decimal("100.00"))
        initial_payment_count = Payment.objects.filter(sale=initial_sale).count()

        grand_total_expected = initial_sale.grand_total # 420
        form_amount_paid = Decimal("300.00") # New total paid amount

        items_post_data = [{'product_id': self.product1.id, 'quantity': "2", 'price': self.product1.price}] # Items unchanged

        edit_url = reverse('retail:sale_edit', kwargs={'pk': initial_sale.pk})
        response = self.client.post(edit_url, data=self._prepare_edit_sale_post_data(initial_sale, items_post_data, form_amount_paid))

        self.assertEqual(response.status_code, 302, response.content)
        updated_sale = Sale.objects.get(pk=initial_sale.pk)

        self.assertEqual(Payment.objects.filter(sale=updated_sale).count(), initial_payment_count + 1)
        latest_payment = Payment.objects.filter(sale=updated_sale).latest('created_at')
        self.assertEqual(latest_payment.amount, form_amount_paid - Decimal("100.00")) # Additional payment: 300 - 100 = 200

        self.assertEqual(updated_sale.amount_paid, form_amount_paid)
        self.assertEqual(updated_sale.payment_status, 'partial')
        self.assertEqual(updated_sale.balance_due, grand_total_expected - form_amount_paid) # 420 - 300 = 120

    def test_edit_sale_form_amount_paid_less_than_actual_no_new_payment(self):
        items_config = [{'product': self.product1, 'quantity': Decimal("1"), 'price': self.product1.price}] # P1: 200, Tax: 10 => GT: 210
        initial_payment_amount = Decimal("150.00")
        initial_sale = self._create_initial_sale(items_config, initial_payment_amount=initial_payment_amount)
        self.assertEqual(initial_sale.amount_paid, initial_payment_amount)
        initial_payment_count = Payment.objects.filter(sale=initial_sale).count()

        form_amount_paid_less = Decimal("100.00") # Form says 100, but actual paid is 150

        items_post_data = [{'product_id': self.product1.id, 'quantity': "1", 'price': self.product1.price}] # Items unchanged

        edit_url = reverse('retail:sale_edit', kwargs={'pk': initial_sale.pk})
        response = self.client.post(edit_url, data=self._prepare_edit_sale_post_data(initial_sale, items_post_data, form_amount_paid_less))

        self.assertEqual(response.status_code, 302, response.content)
        updated_sale = Sale.objects.get(pk=initial_sale.pk)

        self.assertEqual(Payment.objects.filter(sale=updated_sale).count(), initial_payment_count) # No new payment
        self.assertEqual(updated_sale.amount_paid, initial_payment_amount) # Remains 150
        self.assertEqual(updated_sale.payment_status, 'partial')
        self.assertEqual(updated_sale.balance_due, initial_sale.grand_total - initial_payment_amount) # 210 - 150 = 60
