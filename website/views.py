from django.shortcuts import render

def index(request):
    """
    Renders the index.html template for the website app.
    """
    return render(request, 'website/index.html')
