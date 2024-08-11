from django.urls import path,include
from.import views

urlpatterns = [
    path('allEvents',views.allEvents,name='allEvents'),
    path('addEvents',views.addEvents,name='addEvents')

    
]