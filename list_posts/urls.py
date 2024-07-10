from django.urls import path,include
from.import views

urlpatterns = [
    path('list_posts/',views.list_posts, name='list_posts')

    
]