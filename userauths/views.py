from django.shortcuts import render, redirect
from django.urls import reverse # Added for reverse()
from django.contrib.auth.hashers import make_password # Not used in new view, but keep for existing
from django.contrib import messages
from userauths.models import User # UserProfile might be implicitly handled via user.profile
# from business.models import Business # Not directly needed if using user.profile.business
from django.contrib.auth import authenticate, login as auth_login, logout

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm-password")

        # Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect("userauths:register") 

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists!")
            return redirect("userauths:register")
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect("userauths:register")

        # Save user
        user = User(
            username=username,
            email=email,
        )
        user.set_password(password)
        user.save()

        messages.success(request, "Account created successfully!")
        return redirect("userauths:login")

    return render(request, "userauths/signup.html")


def login_view(request):
    if request.method == "POST":
        # email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")
        
        # Authenticate user manually
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):  
                login(request, user) 
                return redirect("core:index")
                # return render(request, "core/index.html") 
            else:
                messages.error(request, "Invalid username or password.")
        except User.DoesNotExist:
            messages.error(request, "Invalid username or password.")

    return render(request, "userauths/login.html")


def logout_view(request):
    logout(request)  # Log out the user
    messages.success(request, "You have successfully logged out.")
    return redirect("userauths:login")


def retail_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            is_retail_user = False
            try:
                # Check for profile, then business, then business type.
                # Ensures no AttributeError if profile or business is None.
                profile = getattr(user, 'profile', None)
                if profile:
                    business = getattr(profile, 'business', None)
                    if business: # Check if business object exists
                        business_type_str = getattr(business, 'type', None)
                        if business_type_str: # Check if the type string is not None or empty
                            if business_type_str.strip().lower() == 'retail':
                                is_retail_user = True
            except Exception:
                # Catch any potential DoesNotExist from related fields if not pre-fetched
                # or other unexpected errors during attribute access.
                # In a real scenario, this should be logged: logger.error("Error accessing profile/business type", exc_info=True)
                pass

            if is_retail_user:
                auth_login(request, user)
                # Assuming 'retail:sales_view' is the correct URL name.
                # This needs to be confirmed from retail/urls.py.
                # Example: return redirect('retail:sales_view')
                # For now, using a placeholder or a common dashboard name.
                # If 'retail:sales_view' is not defined yet, this will error out
                # once a user successfully logs in.
                try:
                    retail_url = reverse('retail:sales_view')
                    return redirect(retail_url)
                except Exception: # Broad exception for NoReverseMatch or other issues
                    messages.warning(request, "Retail dashboard URL not configured, redirecting to main page.")
                    return redirect("core:index") # Fallback redirect
            else:
                messages.error(request, 'Access Denied: This portal is for retail users only, or your profile/business information is incomplete or not set to "retail" type.')
        else:
            messages.error(request, 'Invalid username or password.')

        return render(request, 'userauths/retail_login.html') # Re-render on failed POST

    return render(request, 'userauths/retail_login.html') # Render on GET


