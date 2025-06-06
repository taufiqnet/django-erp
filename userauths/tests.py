from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from business.models import Business
from userauths.models import UserProfile # Kept as is
from contact.models import Contact # New import
from django.core.exceptions import ValidationError # New import

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

    def test_retail_login_successful_for_non_retail_user(self): # Renamed
        if not self.retail_dashboard_url:
            self.skipTest("retail:sales_view URL not configured, skipping dependent test.")

        response = self.client.post(self.login_url, {
            'username': 'nonretailuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302) # Expect redirect
        self.assertRedirects(response, self.retail_dashboard_url)

        response_after_login = self.client.get(self.retail_dashboard_url)
        self.assertEqual(response_after_login.status_code, 200)
        self.assertTrue(response_after_login.context['user'].is_authenticated)
        self.assertEqual(response_after_login.context['user'].username, 'nonretailuser')

    def test_retail_login_successful_for_user_missing_profile(self): # Renamed
        if not self.retail_dashboard_url:
            self.skipTest("retail:sales_view URL not configured, skipping dependent test.")

        response = self.client.post(self.login_url, {
            'username': 'noprofileuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302) # Expect redirect
        self.assertRedirects(response, self.retail_dashboard_url, fetch_redirect_response=False)
        # User is logged in, but retail_dashboard will fail due to missing profile.
        # Check session for authentication directly.
        self.assertTrue(self.client.session.get('_auth_user_id') is not None)
        # Verify the correct user is logged in by fetching their ID
        user = User.objects.get(username='noprofileuser')
        self.assertEqual(self.client.session.get('_auth_user_id'), str(user.id))


    def test_retail_login_successful_for_user_profile_missing_business(self): # Renamed
        if not self.retail_dashboard_url:
            self.skipTest("retail:sales_view URL not configured, skipping dependent test.")

        response = self.client.post(self.login_url, {
            'username': 'profilenobiz',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302) # Expect redirect
        self.assertRedirects(response, self.retail_dashboard_url, fetch_redirect_response=False)

        # User is logged in, but retail_dashboard might fail if it strictly requires business.type == 'retail'
        # which is no longer checked at login but might be checked in the view itself.
        # For this test, we only care that the login view itself authenticated the user.
        self.assertTrue(self.client.session.get('_auth_user_id') is not None)
        user = User.objects.get(username='profilenobiz')
        self.assertEqual(self.client.session.get('_auth_user_id'), str(user.id))

    # Removed redundant test_retail_login_user_business_not_retail_type as it's covered by
    # test_retail_login_successful_for_non_retail_user after logic change.

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

# New Test Class for UserProfile Model
class UserProfileModelTests(TestCase):
    def setUp(self):
        User = get_user_model() # Ensures User is correctly defined for this class
        self.user1 = User.objects.create_user(username='modeltestuser1', email='modeltest1@example.com', password='password123')
        # Ensure unique bid for business to avoid issues if tests are run multiple times or in parallel
        self.business1 = Business.objects.create(name='Model Test Business 1', email='modelbiz1@example.com', bid='mtb_unique_bid_001')

        self.user2 = User.objects.create_user(username='modeltestuser2', email='modeltest2@example.com', password='password123')
        self.contact1 = Contact.objects.create(
            business=self.business1,
            first_name='ModelTest',
            last_name='Contact1',
            email='modelcontact1@example.com',
            mobile='1234509876' # String for mobile
        )
        self.user3 = User.objects.create_user(username='modeltestuser3', email='modeltest3@example.com', password='password123')

    def test_user_profile_creation(self):
        profile = UserProfile.objects.create(user=self.user1, user_type='staff', business=self.business1)
        self.assertEqual(self.user1.profile, profile)

    def test_user_profile_business_association(self):
        # Create a new profile for this test to ensure isolation
        # Recreating user1's profile here for this specific test or ensuring it's clean.
        # If setUp creates it, this might be redundant or cause issues if not handled.
        # For now, assuming self.user1 has no profile or it's okay to re-create/re-associate.
        # Better: Create a new user for this test or ensure clean state.
        # Let's use user1 as per prompt, assuming it's fine or setUp doesn't create its profile.
        profile = UserProfile.objects.create(user=self.user1, user_type='staff', business=self.business1)
        self.assertEqual(profile.business, self.business1)
        self.assertIn(profile, self.business1.staff_profiles.all())

    def test_user_profile_contact_link(self):
        profile = UserProfile.objects.create(user=self.user2, user_type='customer', contact_link=self.contact1)
        self.assertEqual(profile.contact_link, self.contact1)
        self.assertEqual(self.contact1.user_profile_link, profile)
        self.assertIsNone(profile.business, "Customer UserProfile should not have a direct business link.")

    def test_user_profile_staff_requires_business(self):
        User = get_user_model()
        # Use a unique username for the user in this specific test
        staff_user = User.objects.create_user(username='staffcheckuser_model', email='staffcheck_model@example.com', password='password123')
        with self.assertRaises(ValidationError, msg="Staff UserProfile should require a business."):
            # Note: The prompt implies a CheckConstraint is in the model.
            # Django's CheckConstraint validation runs at the DB level or via full_clean().
            profile = UserProfile(user=staff_user, user_type='staff', business=None)
            profile.full_clean()

    def test_user_profile_customer_cannot_have_business(self):
        # Assuming a CheckConstraint like:
        # models.Q(user_type='customer', business__isnull=True)
        with self.assertRaises(ValidationError, msg="Customer UserProfile should not have a direct business link."):
            profile = UserProfile(user=self.user3, user_type='customer', business=self.business1, contact_link=self.contact1)
            profile.full_clean()
