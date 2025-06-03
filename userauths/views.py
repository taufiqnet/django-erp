from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from userauths.models import User
from django.contrib.auth import login, logout

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


