from django.urls import path
from sales import views

app_name = "sales" 

urlpatterns = [
    path("dashboard-sales/", views.dashboard, name="dashboard-sales"),
    path("create/", views.sales_view, name="sales"),

    # Searching customer in sales.html
    path("customer-search/", views.customer_search, name="customer_search"),

    path('product-search/', views.product_search, name='product_search'),
    
    path("create_order/", views.create_order, name="create_order"),
    path("sales_list/", views.sales_list, name="sales_list"),

    # Edit order
    path("edit_order/<int:order_id>/", views.edit_order, name="edit_order"),

    # Update order
    path("update_order/<int:order_id>/", views.update_order, name="update_order"),
]