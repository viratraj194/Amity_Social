from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile,User
from .forms import addPostsForm
from .models import UserPosts,Like,Notification
from django.contrib import messages
from django.template.defaultfilters import slugify


@login_required(login_url='login')
def list_posts(request):
    user_profile = UserProfile.objects.get(user=request.user)
    user = request.user
    posts = UserPosts.objects.all().order_by('-created_at')
    notifications = Notification.objects.filter(user=request.user, read=False) 
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
            print(post_form.errors)
    else:
        post_form = addPostsForm()
    
    context = {
        'post_form': post_form
    }
    return render(request, 'list_posts/list_posts.html', context)

from django.http import JsonResponse
from django.shortcuts import get_object_or_404


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
                        Notification.objects.create(user=post.user,post = post,actor=user)
                        

                return JsonResponse({'status': 'success', 'liked': liked})

            except UserPosts.DoesNotExist:
                return JsonResponse({'status': 'failed', 'message': 'This post does not exist'})

        else:
            return JsonResponse({'status': 'failed', 'message': 'Invalid request'})

    else:
        return JsonResponse({'status': 'failed', 'message': 'Please login to continue'})

    




# def notification(request):
#     if request.user.is_authenticated:
#         notifications = Notification.objects.filter(user=request.user, read=False)
#         context = {
#             'notifications':notifications
#         }
#         return render(request, 'list_posts/list_posts.html',context)
#     else:
#         return redirect('login')



def mark_notification_as_read(request, notification_id):
    notification = Notification.objects.get(id=notification_id, user=request.user)
    notification.read = True
    notification.save()
    return JsonResponse({'status': 'success'})