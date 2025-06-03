from django.shortcuts import render

def dashboard(request):
    return render(request, 'hrm/dashboard.html')
