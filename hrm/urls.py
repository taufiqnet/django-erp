from django.urls import path
from hrm import views

app_name = "hrm" 

urlpatterns = [

    # Homepage
    path("dashboard-hrm/", views.dashboard, name="dashboard-hrm"),

]
