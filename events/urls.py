from django.urls import path,include
from.import views

urlpatterns = [
    path('allEvents',views.allEvents,name='allEvents'),
    path('addEvents',views.addEvents,name='addEvents'),
    path('userEvents',views.userEvents,name='userEvents'),
    path('eventDetails/<int:event_id>/',views.eventDetails,name='eventDetails'),

    
]