from django.urls import path
from.import views

urlpatterns = [
    path('RegisterUser/',views.RegisterUser,name='RegisterUser'),
]