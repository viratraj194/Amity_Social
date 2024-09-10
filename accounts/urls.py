from django.urls import path,include
from.import views

urlpatterns = [
    path('',views.account),
    path('',include('list_posts.urls')),
    

    path('RegisterUser/',views.RegisterUser,name='RegisterUser'),
    path('login/',views.login,name='login'),
    path('logout/',views.logout,name='logout'),
    path('UserDashboard/',views.UserDashboard,name='UserDashboard'),
    path('SavedPosts/',views.SavedPosts,name='SavedPosts'),
    path('account/',views.account,name='account'),
    path('activate/<uidb64>/<token>/',views.activate,name='activate'),

    path('forgot_password/',views.forgot_password,name='forgot_password'),
    path('reset_password_validator/<uidb64>/<token>/',views.reset_password_validator,name='reset_password_validator'),
    path('reset_password/',views.reset_password,name='reset_password'),


    # post details 
    path('post_details/<slug:post_slug>/',views.post_details,name='post_details'),
    # path('post_details_addComment',views.post_details_addComment,name='post_details_addComment'),
    # deleting the post
    path('deletePost/<slug:post_slug>/',views.deletePost,name='deletePost'),
    path('userProfileSettings/',views.userProfileSettings,name='userProfileSettings'),
    

    # adding following and follow systems
    path('send_follow_request/<int:user_id>/',views.send_follow_request,name='send_follow_request'),
    path('unFollow/<int:user_id>/',views.unFollow,name='unFollow'),
    path('accept-follow-request/<int:request_id>/',views.accept_follow_request, name='accept_follow_request'),
    path('deny-follow-request/<int:request_id>/',views.deny_follow_request, name='deny_follow_request'),


    # message urls 
    path('room/<slug:slug>/', views.room_chat, name='room_chat'),
    path('message/<int:user_id>/', views.message_user, name='message_user'),
    path('messages',views.friend_messages,name='friend_messages'),
    path('get_user_status/<int:user_id>/', views.get_user_status, name='get_user_status'),    



    # list friends 
    path('followers',views.followers, name='followers'),
    path('following',views.following, name='following'),
]