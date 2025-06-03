# urls.py
from django.urls import path
from . import views

app_name = 'pharmacy'

urlpatterns = [
    path('sale/', views.sale_view, name='sale'),
    path('search-products/', views.search_products, name='search_products'),
    path('filter-products/', views.search_products, name='filter_products'),  # Same view as search
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('update-cart-item/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('clear-cart/', views.clear_cart, name='clear_cart'),
    path('complete-sale/', views.complete_sale, name='complete_sale'),
]