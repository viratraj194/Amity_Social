from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.decorators import login_required
from accounts.models import *
from .forms import addPostsForm
from .models import UserPosts,Like,Notification,Comment,UserSavedPosts
from django.contrib import messages
from django.template.defaultfilters import slugify
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .forms import addCommentForm
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator




@login_required(login_url='login')
def list_posts(request):
    user_profile = UserProfile.objects.get(user=request.user)
    user = request.user
    collage = user.collage_name
    posts = UserPosts.objects.filter(user__collage_name=collage).order_by('-created_at')
    total_posts = UserPosts.objects.filter(user=user)
    
    # Sending the follow request
    follow_requests = FollowRequest.objects.filter(to_user=user, is_accepted=False)
    
    # Get all users who are following the logged-in user
    followers = Follower.objects.filter(following=user).select_related('follower')

    # Get all users the logged-in user is following
    following = Follower.objects.filter(follower=user).select_related('following')

    total_following = following.count()
    total_followers = followers.count()
    
    # Add attributes to posts: is_saved, is_portrait, is_liked, is_following
    for post in posts:
        post.saved_by_user = UserSavedPosts.objects.filter(user=request.user, post=post).exists()
        post.is_portrait = post.image_height > post.image_width if post.image_height and post.image_width else False
        post.liked_by_user = post.likes.filter(user=user).exists() if user else False
        post.is_following = Follower.objects.filter(follower=user, following=post.user).exists()  # Add is_following attribute to each post

    notifications = Notification.objects.filter(user=request.user, read=False).order_by('-timestamp')
    # implement pagination
    # if messages 
    user_messages = Message.objects.filter(receiver=request.user,read = False)
    paginator = Paginator(posts,15)
    page = int(request.GET.get('page', 1))
    try:
        posts = paginator.page(page)
    except:
        return HttpResponse('')
    context = {
        'user_profile': user_profile,
        'user': user,
        'posts': posts,  # Pass the modified posts list
        'notifications': notifications,
        'total_posts': total_posts.count(),
        'follow_requests': follow_requests,
        'total_following': total_following,
        'total_followers': total_followers,
        'user_messages':user_messages,
        'page':page,
    }
    if request.headers.get('HX-Request') == 'true':
        return render(request,'list_posts\loop_posts.html',context)
    return render(request, 'list_posts/list_posts.html', context)


@login_required(login_url='login')
def add_posts(request):
    if not request.user.is_approved:
        messages.error(request, 'Your account is not approved to post.')
        return redirect('list_posts')
    if request.method == 'POST':
        post_form = addPostsForm(request.POST, request.FILES)
        if post_form.is_valid():
            post = post_form.save(commit=False)  # Don't save to the database yet
            post.user = request.user  # Set the user to the current logged-in user

            if not post.content and not post.caption and not post.post_image:
                messages.error(request, "You cannot post an empty post. Please provide content, caption, or an image.")
                return redirect('list_posts')
            post.save()  # Save the post now

            # Set post_slug based on user's name and post id
            user = request.user
            user_name = f'{user.first_name}{user.last_name}'
            post.post_slug = slugify(user_name) + '_' + str(post.id)
            post.save()  # Save the post again to update post_slug

            messages.success(request, 'New post is added.')
            return redirect('list_posts')
        else:
            
            messages.error(request,'Post caption is to big or corrupted image')
            return redirect('list_posts')
            
    else:
        post_form = addPostsForm()
    
    context = {
        'post_form': post_form
    }
    return render(request, 'list_posts/list_posts.html', context)

@login_required(login_url='login')
def mark_notification_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.read = True
    notification.delete()
    notification.save()
    return JsonResponse({'status': 'success'})







@csrf_exempt
def add_comment(request, post_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        comment_text = data.get('comment', 'No comment provided')
        post_id = data.get('post_id', 'None')
        user = request.user

        if comment_text:
            post = UserPosts.objects.get(id=post_id)
            comment = Comment.objects.create(post=post, user=user, comment=comment_text)

            response_data = {
                'success': True,
                'comment': {
                    'text': comment.comment,
                    'user': comment.user.username,
                    'profile_picture': comment.user.userprofile.profile_picture.url,
                    'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'success': False, 'message': 'Invalid form data.'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



# showing comments

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import UserPosts, Comment
@login_required(login_url='login')
def get_comments(request, post_id):
    post = get_object_or_404(UserPosts, id=post_id)
    comments = Comment.objects.filter(post=post).select_related('user__userprofile')
    user = request.user
    # Create a notification for the post's author
    if post.user != user:
        Notification.objects.create(
                    user=post.user,
                    post=post,
                    notification_msg="Commented on your post",
                    actor=user,
                    read=False
            )
        

    comments_data = [
        {
            'user': comment.user.username,
            'profile_picture': comment.user.userprofile.profile_picture.url,
            'comment': comment.comment,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        for comment in comments
    ]  
    return JsonResponse({'comments': comments_data})

@login_required(login_url='login')
def post_like(request, post_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                post = get_object_or_404(UserPosts, id=post_id)
                user = request.user

                if Like.objects.filter(user=user, post=post).exists():
                    # If already liked, remove the like
                    Like.objects.filter(user=user, post=post).delete()
                    liked = False
                else:
                    # If not liked, create a new like
                    Like.objects.create(user=user, post=post)
                    liked = True
                    if post.user != user:
                        Notification.objects.create(user=post.user,post = post,actor=user, notification_msg='Liked your Post.')
                        

                return JsonResponse({'status': 'success', 'liked': liked})

            except UserPosts.DoesNotExist:
                return JsonResponse({'status': 'failed', 'message': 'This post does not exist'})

        else:
            return JsonResponse({'status': 'failed', 'message': 'Invalid request'})

    else:
        return JsonResponse({'status': 'failed', 'message': 'Please login to continue'})


@login_required(login_url='login')
def save_post(request, post_id):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            post = get_object_or_404(UserPosts, id=post_id)
            
            user = request.user
            if UserSavedPosts.objects.filter(user=user, post=post).exists():
                UserSavedPosts.objects.filter(user=user, post=post).delete()
                post_saved = False
            else:
                UserSavedPosts.objects.create(user=user, post=post)
                post_saved = True
            return JsonResponse({'status': 'success', 'post_saved': post_saved})
        except UserPosts.DoesNotExist:
            return JsonResponse({'status': 'failed', 'message': 'Post does not exist'})
    else:
        return JsonResponse({'status': 'failed', 'message': 'Invalid request'})



# user profile details

@login_required(login_url='login')
def profile_details(request,user_id):
    user = request.user
    profile = get_object_or_404(User,id=user_id)

    # Get all users who are following the logged-in user
    followers = Follower.objects.filter(following=profile).select_related('follower')
    # Get all users the logged-in user is following
    following = Follower.objects.filter(follower=profile).select_related('following')
    # list event in hte dashboard

    # Check if the logged-in user is following the profile user
    is_following = Follower.objects.filter(follower=user, following=profile).exists()
    posts = UserPosts.objects.filter(user=profile)

    

    # all total 
    total_following = following.count()
    total_followers = followers.count()
    total_posts = posts.count()
    context = {
        'profile':profile,
        'total_posts':total_posts,
        'total_following':total_following,
        'total_followers':total_followers,
        'is_following':is_following,
    }
    return render(request,'list_posts/profile_details.html',context)




from django.urls import reverse
@login_required(login_url='login')
def search_user(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' and request.method == "GET":
        users_id = request.GET.get('users_id', None)
        if users_id:
            user = get_object_or_404(User, users_id=users_id)
            profile_url = reverse('profile_details', args=[user.id])  # Dynamically create the profile URL
            data = {
                'user_id': user.id,
                'users_id': user.users_id,
                'username': user.username,
                'bio': user.userprofile.userBio,
                'profile_picture': user.userprofile.profile_picture.url if user.userprofile.profile_picture else None,
                'profile_url': profile_url,  # Add the profile URL to the response
            }
            return JsonResponse(data, status=200)
        else:
            return JsonResponse({'error': 'User not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)



