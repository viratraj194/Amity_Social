from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile,User
from .forms import addPostsForm
from .models import UserPosts,Like,Notification,Comment,UserSavedPosts
from django.contrib import messages
from django.template.defaultfilters import slugify
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .forms import addCommentForm







@login_required(login_url='login')
def list_posts(request):
    user_profile = UserProfile.objects.get(user=request.user)
    user = request.user
    posts = UserPosts.objects.all().order_by('-created_at')
    for post in posts:
        post.saved_by_user = UserSavedPosts.objects.filter(user=request.user, post=post).exists()
    notifications = Notification.objects.filter(user=request.user, read=False).order_by('-timestamp')
    for post in posts:
        if post.image_height is not None and post.image_width is not None:
            post.is_portrait = post.image_height > post.image_width
        else:
            post.is_portrait = False  # Default to landscape if dimensions are missing
            
        for post in posts:
            post.liked_by_user = post.likes.filter(user=user).exists() if user else False

    context = {
        'user_profile':user_profile,
        'user':user,
        'posts':posts,
        'notifications':notifications,

    }
    return render(request,'list_posts/list_posts.html',context)


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
            
            messages.error(request,'POST Image is not valid image or its corrupted image')
            return redirect('list_posts')
            
    else:
        post_form = addPostsForm()
    
    context = {
        'post_form': post_form
    }
    return render(request, 'list_posts/list_posts.html', context)


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
