from django.urls import path,include
from.import views

urlpatterns = [
    path('list-posts/',views.list_posts, name='list_posts'),
    path('add-posts/',views.add_posts,name='add_posts'),
    path('post_like/<int:post_id>/', views.post_like, name='post_like'),
    

    
]