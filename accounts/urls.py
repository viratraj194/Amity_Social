from django.urls import path
from.import views

urlpatterns = [
    path('RegisterUser/',views.RegisterUser,name='RegisterUser'),
    path('login/',views.login,name='login'),
    path('logout/',views.logout,name='logout'),
    path('UserDashboard/',views.UserDashboard,name='UserDashboard'),
    path('account/',views.account,name='account'),
    path('activate/<uidb64>/<token>/',views.activate,name='activate')
]