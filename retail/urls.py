from django.urls import path
from retail import views

app_name = "retail" 

urlpatterns = [
    path("create/", views.sales_view, name="sales_view"), # Changed name from "sale" to "sales_view"
    path('process-sale/', views.process_sale, name='process_sale'),
    path('sales/', views.sale_list, name='sale_list'),
    path('sales/<int:sale_id>/', views.sale_detail, name='sale_detail'),
    path('sales/<int:pk>/edit/', views.sale_edit, name='sale_edit'),
    path('sales/<int:sale_id>/print/', views.print_receipt, name='print_receipt'),
    path('add-customer/', views.add_customer, name='add_customer'),
    path('api/customers/', views.customer_list, name='customer_list'),
]