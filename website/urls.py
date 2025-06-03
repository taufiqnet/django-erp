from django.urls import path
from website import views

app_name = "website" 

urlpatterns = [

    # Homepage
    path("", views.index, name="index"),

]
