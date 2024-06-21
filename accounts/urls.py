from django.urls import path
from.import views

urlpatterns = [
    path('RegisterUser/',views.RegisterUser,name='RegisterUser'),
    path('login/',views.login,name='login'),
    path('logout/',views.logout,name='logout'),
    path('account/',views.account,name='account'),
]