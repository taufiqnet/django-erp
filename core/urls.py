from django.urls import path
from core import views

app_name = "core" 

urlpatterns = [

    # Homepage
    path("", views.index, name="index"),

    # Multivendor Homepage / Index page
    path("multivendor/", views.multivendorIndex, name="multivendor"),

    # Business Type based path : food or beauty
    path("foods/", views.business_type_food, name="food-products"),

    # path("products/", views.product_list_view, name="product-list"),
    path('products/<str:business_type>/', views.product_list_view, name='product-list'),

    # Multivendor product list
    path('products/', views.multivendor_product_list_view, name='multivendor-product-list'),

    # path("product/<pid>", views.product_detail_view, name="product-detail"),
    path('product/<slug:slug>/', views.product_detail_view, name='product-detail'),

    # Category
    path("category/", views.category_list_view, name="category-list"),
    # path("category/<cid>", views.category_product_list_view, name="category-product-list"),
    path("category/<slug:slug>", views.category_product_list_view, name="category-product-list"),


    # Tags
    path('products/tag/<slug:tag_slug>/', views.tag_list_view, name="tags"),

    # Search
    path('search/', views.search_view, name="search"),

    # Add to Cart
    path('add-to-cart/', views.add_to_cart, name="add-to-cart"),

    # Checkout
    path("checkout/", views.checkout_view, name="checkout"),
    path("update-cart/", views.update_cart, name="update-cart"),

    # Order Confirmation
    path('order-confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),

    # Download Invoice
    path('download-invoice/<int:order_id>/', views.download_invoice, name='download_invoice'),


]
