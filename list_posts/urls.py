from django.urls import path,include
from.import views

urlpatterns = [
    path('list-posts/',views.list_posts, name='list_posts'),
    path('add-posts/',views.add_posts,name='add_posts'),
    path('post_like/<int:post_id>/', views.post_like, name='post_like'),

    # test notification 
    # path('notification/',views.notification, name='notification')
    path('mark_notification_as_read/<int:notification_id>/', views.mark_notification_as_read, name='mark_notification_as_read'),
    path('add_comment/<int:post_id>/',views.add_comment,name='add_comment'),


    path('comments/<int:post_id>/', views.get_comments, name='get_comments'),
    path('save_post/<int:post_id>/',views.save_post,name='save_post'),

    # profile details
    path('profile_details/<int:user_id>/',views.profile_details,name='profile_details'),
    # path('message/<int:user_id>/', views.message_user, name='message_user'),
    
    # search users 
    path('search-user/', views.search_user, name='search_user'), 
    
]