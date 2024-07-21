from django.urls import path,include
from.import views

urlpatterns = [
    path('',views.account),


    path('RegisterUser/',views.RegisterUser,name='RegisterUser'),
    path('login/',views.login,name='login'),
    path('logout/',views.logout,name='logout'),
    path('UserDashboard/',views.UserDashboard,name='UserDashboard'),
    path('account/',views.account,name='account'),
    path('activate/<uidb64>/<token>/',views.activate,name='activate'),

    path('forgot_password/',views.forgot_password,name='forgot_password'),
    path('reset_password_validator/<uidb64>/<token>/',views.reset_password_validator,name='reset_password_validator'),
    path('reset_password/',views.reset_password,name='reset_password'),


    path('userProfileSettings/',views.userProfileSettings,name='userProfileSettings'),

    path('',include('list_posts.urls')),

    
]