# pharmacy/urls.py - Make sure all these URLs are properly configured

from django.urls import path
from . import views

app_name = 'pharmacy'

urlpatterns = [
    # Main sales page
    path('sales/', views.sale_view, name='sales_page'),
    
    # Cart operations
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart-quantity/<int:product_id>/', views.update_cart_quantity, name='update_cart_quantity'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    
    # Product search and filtering
    path('search-products/', views.search_products, name='search_products'),
    path('filter-products/', views.filter_products, name='filter_products'),
    
    # Sale completion
    path('complete-sale/', views.complete_sale, name='complete_sale'),
    
    # Add other URLs as needed
]