from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from business.models import Business
from userauths.models import UserProfile

User = get_user_model()

class RetailLoginViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('userauths:retail_login')

        # Attempt to reverse retail:sales_view, handle if not found during setup
        try:
            self.retail_dashboard_url = reverse('retail:sales_view')
        except Exception:
            self.retail_dashboard_url = None # Will cause tests needing this to fail, or skip them

        # Retail Business and User
        self.retail_business = Business.objects.create(
            name="Test Retail Co",
            type="retail",
            email="retail@example.com",
            bid="RETAILBID" # Assuming bid is required and unique
        )
        self.retail_user = User.objects.create_user(
            username='retailuser',
            password='password123',
            email='retailuser@example.com'
        )
        self.retail_profile = UserProfile.objects.create(
            user=self.retail_user,
            business=self.retail_business,
            user_type='staff'
        )

        # Non-Retail Business and User
        self.non_retail_business = Business.objects.create(
            name="Test NonRetail Co",
            type="other", # Not 'retail'
            email="other@example.com",
            bid="OTHERBID"
        )
        self.non_retail_user = User.objects.create_user(
            username='nonretailuser',
            password='password123',
            email='nonretailuser@example.com'
        )
        self.non_retail_profile = UserProfile.objects.create(
            user=self.non_retail_user,
            business=self.non_retail_business,
            user_type='staff'
        )

        # User with missing profile information
        self.user_no_profile_data = User.objects.create_user(
            username='noprofileuser',
            password='password123',
            email='noprofile@example.com'
        )
        # No UserProfile created for this user

        self.user_profile_no_business = User.objects.create_user(
            username='profilenobiz',
            password='password123',
            email='profilenobiz@example.com'
        )
        UserProfile.objects.create(user=self.user_profile_no_business, user_type='customer', business=None) # Changed user_type to 'customer'

        # User for testing case-insensitive and whitespace stripping for business type
        self.case_test_business = Business.objects.create(
            name="Case Test Retail Co",
            type=" Retail ", # Note: leading/trailing spaces and mixed case
            email="casetest@example.com",
            bid="CASETBID"
        )
        self.case_test_user = User.objects.create_user(
            username='casetestuser',
            password='password123',
            email='casetest@example.com'
        )
        self.case_test_profile = UserProfile.objects.create(
            user=self.case_test_user,
            business=self.case_test_business,
            user_type='staff'
        )

    def test_retail_login_page_loads_get_request(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'userauths/retail_login.html')

    def test_retail_login_successful_retail_user(self):
        if not self.retail_dashboard_url:
            self.skipTest("retail:sales_view URL not configured, skipping dependent test.")

        response = self.client.post(self.login_url, {
            'username': 'retailuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.retail_dashboard_url)

        # Check user is authenticated by trying to access a protected page or checking session
        # After login, the client's session will have the user ID.
        # A simple way is to see if we can GET the dashboard again, now successfully
        response_after_login = self.client.get(self.retail_dashboard_url)
        self.assertEqual(response_after_login.status_code, 200) # Assuming it's a 200 OK page
        self.assertTrue(response_after_login.context['user'].is_authenticated)


    def test_retail_login_failed_invalid_credentials(self):
        response = self.client.post(self.login_url, {
            'username': 'retailuser',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200) # Re-renders login page
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any(message.message == 'Invalid username or password.' for message in messages))
        self.assertFalse(self.client.session.get('_auth_user_id')) # Check user not logged in

    def test_retail_login_failed_non_retail_user(self):
        response = self.client.post(self.login_url, {
            'username': 'nonretailuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200) # Re-renders login page
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Access Denied' in message.message for message in messages))
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_retail_login_user_missing_profile(self):
        response = self.client.post(self.login_url, {
            'username': 'noprofileuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Access Denied' in message.message for message in messages))
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_retail_login_user_profile_missing_business(self):
        response = self.client.post(self.login_url, {
            'username': 'profilenobiz',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Access Denied' in message.message for message in messages))
        self.assertFalse(self.client.session.get('_auth_user_id'))

    def test_retail_login_user_business_not_retail_type(self):
        # This is effectively the same as test_retail_login_failed_non_retail_user
        # but can be made more explicit if business.type check is subtle.
        # Re-using non_retail_user for clarity of intent.
        response = self.client.post(self.login_url, {
            'username': self.non_retail_user.username,
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Access Denied' in message.message for message in messages))
        self.assertFalse(self.client.session.get('_auth_user_id'))


    def test_unauthenticated_access_to_protected_retail_view(self):
        if not self.retail_dashboard_url:
            self.skipTest("retail:sales_view URL not configured, skipping dependent test.")

        # Ensure client is logged out first
        self.client.logout()

        response = self.client.get(self.retail_dashboard_url)
        self.assertEqual(response.status_code, 302) # Redirect
        # Check if the redirect URL's path matches the login URL's path
        # This handles potential query parameters like ?next=...
        self.assertTrue(self.login_url in response.url)
        self.assertEqual(response.url.split('?')[0], self.login_url)

    def test_retail_login_successful_case_insensitive_whitespace_business_type(self):
        if not self.retail_dashboard_url:
            self.skipTest("retail:sales_view URL not configured, skipping dependent test.")

        response = self.client.post(self.login_url, {
            'username': 'casetestuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302, response.content) # Show content on failure
        self.assertRedirects(response, self.retail_dashboard_url)

        response_after_login = self.client.get(self.retail_dashboard_url)
        self.assertEqual(response_after_login.status_code, 200)
        self.assertTrue(response_after_login.context['user'].is_authenticated)
        self.assertEqual(response_after_login.context['user'].username, 'casetestuser')
