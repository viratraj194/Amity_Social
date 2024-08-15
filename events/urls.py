from django.urls import path,include
from.import views

urlpatterns = [
    path('allEvents',views.allEvents,name='allEvents'),
    path('addEvents',views.addEvents,name='addEvents'),
    path('userEvents',views.userEvents,name='userEvents'),
    path('eventDetails/<int:event_id>/',views.eventDetails,name='eventDetails'),
    path('editEvent/<int:event_id>/',views.editEvent,name='editEvent'),
    path('deleteEvent/<int:event_id>/',views.deleteEvent,name='deleteEvent'),
    
]