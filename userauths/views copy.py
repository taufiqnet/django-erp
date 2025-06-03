from django.shortcuts import render, redirect
from django.contrib import messages
from .models import User, UserProfile

def register_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm-password")
        user_type = request.POST.get("user_type")  # Retrieve user type from form

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

        if user_type not in ['customer', 'vendor']:
            messages.error(request, "Invalid user type selected!")
            return redirect("userauths:register")

        # Save user
        user = User(
            username=username,
            email=email,
        )
        user.set_password(password)
        user.save()

        # Save user profile with the selected user type
        UserProfile.objects.create(
            user=user,
            user_type=user_type,
            # Set default values for fields based on user type
            customer_tier='regular' if user_type == 'customer' else None,
            allowed_business_type='beauty' if user_type == 'vendor' else None,
        )

        messages.success(request, "Account created successfully!")
        return redirect("userauths:login")

    return render(request, "userauths/signup.html")
