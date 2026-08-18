from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.models import *
from .forms import addPostsForm
from .models import UserPosts,Like,Notification,Comment,UserSavedPosts,PostReport
from django.contrib import messages
from django.template.defaultfilters import slugify
from django.utils.html import strip_tags
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .forms import addCommentForm
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.core.paginator import Paginator
from accounts.models import Message
from django_ratelimit.decorators import ratelimit
from django_ratelimit.exceptions import Ratelimited
from django.template.response import TemplateResponse
from django.views.decorators.http import require_POST
from django.db.models import Count
from django.core.mail import send_mail




@login_required(login_url='login')
def list_posts(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    user = request.user
    college_id = user.college.id if user.college else None

    page = int(request.GET.get('page', 1))
    cache_key = f'posts_list_{request.user.id}_{college_id}_page_{page}'

    # Try cache first (non-HTMX requests only)
    cached_data = cache.get(cache_key)
    if cached_data and request.headers.get('HX-Request') != 'true':
        return render(request, 'list_posts/list_posts.html', cached_data)

    posts = UserPosts.objects.filter(user__college_id=college_id).select_related('user__userprofile').prefetch_related('comments__user').order_by('-created_at')
    total_posts = UserPosts.objects.filter(user=user)

    # Sending the follow request
    follow_requests = FollowRequest.objects.filter(to_user=user, is_accepted=False)
    
    # Get all users who are following the logged-in user
    followers = Follower.objects.filter(following=user).select_related('follower')

    # Get all users the logged-in user is following
    following = Follower.objects.filter(follower=user).select_related('following')

    total_following = following.count()
    total_followers = followers.count()

    # Prefetch following list for efficient lookup
    following_users = set(Follower.objects.filter(follower=user).values_list('following_id', flat=True))

    # Prefetch saved posts and likes for the user
    saved_posts = set(UserSavedPosts.objects.filter(user=request.user).values_list('post_id', flat=True))
    liked_posts = set(Like.objects.filter(user=user).values_list('post_id', flat=True))

    # Add attributes to posts: is_saved, is_portrait, is_liked, is_following
    # Only process posts that will be displayed (after pagination)
    notifications = Notification.objects.filter(user=request.user, read=False).order_by('-timestamp')
    user_messages = Message.objects.filter(receiver=request.user, status__lt=Message.STATUS_READ)
    paginator = Paginator(posts,15)
    try:
        posts = paginator.page(page)
    except:
        return HttpResponse('')

    # Now enrich only the displayed posts
    for post in posts:
        post.saved_by_user = post.id in saved_posts
        post.is_portrait = post.image_height > post.image_width if post.image_height and post.image_width else False
        post.liked_by_user = post.id in liked_posts
        post.is_following = post.user.id in following_users

    context = {
        'user_profile': user_profile,
        'user': user,
        'posts': posts,
        'notifications': notifications,
        'total_posts': total_posts.count(),
        'follow_requests': follow_requests,
        'total_following': total_following,
        'total_followers': total_followers,
        'user_messages':user_messages,
        'page':page,
    }

    # Cache for 30 seconds (non-HTMX only)
    if request.headers.get('HX-Request') != 'true':
        cache.set(cache_key, context, 30)

    if request.headers.get('HX-Request') == 'true':
        return render(request,'list_posts/loop_posts.html',context)
    return render(request, 'list_posts/list_posts.html', context)


@login_required(login_url='login')
def add_posts(request):
    if not request.user.is_approved:
        messages.error(request, 'Your account is not approved to post.')
        return redirect('list_posts')
    if request.method == 'POST':
        post_form = addPostsForm(request.POST, request.FILES)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.user = request.user

            if not post.content and not post.caption and not post.post_image:
                messages.error(request, "You cannot post an empty post. Please provide content, caption, or an image.")
                return redirect('list_posts')
            try:
                post.save()

                # Set post_slug based on user's name and post id
                user = request.user
                user_name = f'{user.first_name}{user.last_name}'
                post.post_slug = slugify(user_name) + '_' + str(post.id)
                post.save()

                # Invalidate cache for the user's college feed
                college_id = request.user.college.id if request.user.college else None
                cache.delete(f'posts_list_{request.user.id}_{college_id}_page_1')
                messages.success(request, 'New post is added.')
                return redirect('list_posts')
            except Exception:
                messages.error(request, 'Failed to upload image. Please try again later.')
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



# Delete post view
def delete_post(request, post_id):
    post = get_object_or_404(UserPosts, id=post_id)

    if request.user != post.user:
        messages.error(request, 'You do not have permission to delete this post.')
        return redirect('post_details', post_slug=post.post_slug)

    post.delete()
    # Invalidate cache for the user's college feed
    college_id = request.user.college.id if request.user.college else None
    cache.delete(f'posts_list_{request.user.id}_{college_id}_page_1')           
    messages.success(request, 'Post has been deleted.')
    return redirect('list_posts')









@login_required(login_url='login')
def mark_notification_as_read(request, notification_id):
    # SECURITY: Validate notification_id is a positive integer
    try:
        notification_id = int(notification_id)
        if notification_id <= 0:
            return JsonResponse({'status': 'invalid_id', 'message': 'Invalid notification ID'})
    except (ValueError, TypeError):
        return JsonResponse({'status': 'invalid_id', 'message': 'Invalid notification ID format'})

    # SECURITY: Ownership check - ensure notification belongs to requesting user
    notification = Notification.objects.filter(id=notification_id, user=request.user).first()

    if not notification:
        return JsonResponse({'status': 'already_handled', 'message': 'Notification not found or already processed'})

    notification.delete()

    # Invalidate cache for the user to remove stale notification
    college_id = request.user.college.id if request.user.college else None
    if college_id:
        cache.delete(f'posts_list_{request.user.id}_{college_id}_page_1')

    return JsonResponse({'status': 'success'})


@login_required(login_url='login')
def mark_all_as_read(request):
    if request.method == "POST":
        Notification.objects.filter(user=request.user, read=False).delete()
        # Invalidate cache to ensure fresh data on next load
        college_id = request.user.college.id if request.user.college else None
        if college_id:
            cache.delete(f'posts_list_{request.user.id}_{college_id}_page_1')
        return JsonResponse({"success": True, "message": "All notifications cleared."})
    return JsonResponse({"success": False, "message": "Invalid request"}, status=400)







@login_required(login_url='login')
@ratelimit(key='user', rate='10/m', block=True, method=['POST'])
def add_comment(request, post_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON data'})

        comment_text = data.get('comment', '').strip()
        post_id = data.get('post_id')
        parent_id = data.get('parent_id', None)

        # SECURITY: Validate comment text - sanitize HTML tags to prevent XSS
        if not comment_text:
            return JsonResponse({'success': False, 'message': 'Comment text is required'})

        # Strip HTML tags to prevent XSS attacks
        comment_text = strip_tags(comment_text)

        # Validate comment length (prevent DoS via huge payloads)
        if len(comment_text) > 5000:
            return JsonResponse({'success': False, 'message': 'Comment too long (max 5000 characters)'})

        # SECURITY: Validate post_id is a positive integer
        try:
            post_id = int(post_id)
            if post_id <= 0:
                return JsonResponse({'success': False, 'message': 'Invalid post ID'})
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'message': 'Invalid post ID format'})

        user = request.user
        post = get_object_or_404(UserPosts, id=post_id)

        # If parent_id provided, verify it exists and belongs to same post
        parent = None
        if parent_id:
            try:
                parent_id = int(parent_id)
                if parent_id <= 0:
                    parent = None
                else:
                    parent = Comment.objects.filter(id=parent_id, post=post).first()
            except (ValueError, TypeError):
                parent = None

        comment = Comment.objects.create(
            post=post,
            user=user,
            comment=comment_text,
            parent=parent
        )

        # Create notification for post author (if not self-comment)
        if post.user != user:
            # Only create notification if one doesn't already exist for this comment
            if not Notification.objects.filter(user=post.user, post=post, actor=user, notification_msg='Commented on your post').exists():
                Notification.objects.create(
                    user=post.user,
                    post=post,
                    notification_msg='Commented on your post',
                    actor=user,
                    read=False
                )

        response_data = {
            'success': True,
            'comment': {
                'id': comment.id,
                'comment': comment.comment,
                'user': comment.user.username,
                'profile_picture': comment.user.userprofile.profile_picture.url if hasattr(comment.user, 'userprofile') and comment.user.userprofile.profile_picture else '/static/img/images.jpeg',
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'parent_id': comment.parent.id if comment.parent else None,
                'is_reply': comment.is_reply
            }
        }
        return JsonResponse(response_data)

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})



# showing comments

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import UserPosts, Comment

@login_required(login_url='login')
def get_comments(request, post_id):
    from django.core.paginator import Paginator
    import html

    # SECURITY: Validate post_id is a positive integer
    try:
        post_id = int(post_id)
        if post_id <= 0:
            return JsonResponse({'error': 'Invalid post ID'}, status=400)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid post ID format'}, status=400)

    post = get_object_or_404(UserPosts, id=post_id)
    page = int(request.GET.get('page', 1))

    # Get top-level comments (no parent) with optimized prefetching for replies
    top_level_comments = Comment.objects.filter(
        post=post, parent__isnull=True
    ).select_related(
        'user', 'user__userprofile'
    ).prefetch_related(
        'replies__user', 'replies__user__userprofile'
    ).order_by('-created_at')

    # Paginate to 20 comments per page
    paginator = Paginator(top_level_comments, 20)

    try:
        comments_page = paginator.page(page)
    except:
        return JsonResponse({'comments': [], 'has_more': False, 'total_pages': 0, 'current_page': 1})

    user = request.user

    # Get following users set for comment visibility check
    following_users = set(Follower.objects.filter(follower=user).values_list('following_id', flat=True))

    def serialize_comment(comment):
        """Serialize a comment and its replies"""
        show_user_info = comment.user.id in following_users
        comment_data = {
            'id': comment.id,
            'user': comment.user.username if show_user_info else 'Private User',
            'profile_picture': comment.user.userprofile.profile_picture.url if show_user_info and hasattr(comment.user, 'userprofile') and comment.user.userprofile.profile_picture else '/static/img/images.jpeg',
            'comment': html.escape(comment.comment),
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'parent_id': comment.parent.id if comment.parent else None,
            'is_reply': comment.is_reply,
            'reply_count': comment.replies.count(),
            'replies': []
        }
        # Use prefetched replies instead of making new queries
        for reply in comment.replies.all():
            reply_show_user_info = reply.user.id in following_users
            comment_data['replies'].append({
                'id': reply.id,
                'user': reply.user.username if reply_show_user_info else 'Private User',
                'profile_picture': reply.user.userprofile.profile_picture.url if reply_show_user_info and hasattr(reply.user, 'userprofile') and reply.user.userprofile.profile_picture else '/static/img/images.jpeg',
                'comment': html.escape(reply.comment),
                'created_at': reply.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'parent_id': reply.parent.id,
                'is_reply': True
            })
        return comment_data

    comments_data = [serialize_comment(comment) for comment in comments_page.object_list]
    return JsonResponse({
        'comments': comments_data,
        'has_more': comments_page.has_next(),
        'total_pages': paginator.num_pages,
        'current_page': page
    })

from django.db import transaction

@login_required(login_url='login')
@ratelimit(key='user', rate='15/m', block=True, method=['POST'])
def post_like(request, post_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                post = get_object_or_404(UserPosts, id=post_id)
                user = request.user

                with transaction.atomic():
                    # Use get_or_create for atomic toggle operation
                    like, created = Like.objects.get_or_create(user=user, post=post)
                    if created:
                        liked = True
                        # Only create notification if one doesn't already exist for this like
                        if post.user != user and not Notification.objects.filter(user=post.user, post=post, actor=user, notification_msg='Liked your Post.').exists():
                            Notification.objects.create(user=post.user, post=post, actor=user, notification_msg='Liked your Post.')
                    else:
                        like.delete()
                        liked = False

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

            with transaction.atomic():
                saved, created = UserSavedPosts.objects.get_or_create(user=user, post=post)
                if created:
                    post_saved = True
                else:
                    saved.delete()
                    post_saved = False

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
            # SECURITY: Validate users_id format (should be numeric)
            try:
                users_id = str(users_id).strip()
                if not users_id.isdigit():
                    return JsonResponse({'error': 'Invalid user ID format'}, status=400)
            except (ValueError, TypeError):
                return JsonResponse({'error': 'Invalid user ID format'}, status=400)

            user = get_object_or_404(User, users_id=users_id)
            profile_url = reverse('profile_details', args=[user.id])
            data = {
                'user_id': user.id,
                'users_id': user.users_id,
                'username': user.username,
                'bio': user.userprofile.userBio,
                'profile_picture': user.userprofile.profile_picture.url if user.userprofile.profile_picture else None,
                'profile_url': profile_url,
            }
            return JsonResponse(data, status=200)
        else:
            return JsonResponse({'error': 'User not found'}, status=404)
    return JsonResponse({'error': 'Invalid request'}, status=400)






#unread_message_count

def unread_message_count(request):
    if request.user.is_authenticated:
        unread_count = Message.objects.filter(receiver=request.user, status__lt=Message.STATUS_READ).count()
        return JsonResponse({"unread_count": unread_count})
    return JsonResponse({"unread_count": 0})


@login_required(login_url='login')
@require_POST
def report_post(request, post_id):
    try:
        post = UserPosts.objects.get(id=post_id)
    except UserPosts.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Post not found.'}, status=404)
        
    try:
        data = json.loads(request.body)
        reason = data.get('reason', '')
        description = data.get('description', '')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data.'}, status=400)
        
    report, created = PostReport.objects.get_or_create(
        reporter=request.user,
        post=post,
        defaults={'reason': reason, 'description': description}
    )
    
    if not created:
        return JsonResponse({'success': False, 'message': 'You have already reported this post.'}, status=400)
        
    return JsonResponse({'success': True, 'message': 'Post reported successfully.'}, status=200)


@login_required(login_url='login')
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_moderation_feed(request):
    posts = UserPosts.objects.annotate(report_count=Count('reports')).filter(report_count__gte=2).prefetch_related('reports', 'user')
    context = {'posts': posts}
    return render(request, 'list_posts/admin_reports_page.html', context)


@login_required(login_url='login')
@require_POST
@user_passes_test(lambda u: u.is_staff)
def api_delete_flagged_post(request, post_id):
    from django.conf import settings
    from django.core.mail import send_mail
    post = get_object_or_404(UserPosts, id=post_id)
    
    reasons = list(post.reports.values_list('reason', flat=True).distinct())
    
    reason_map = {
        'nudity': 'Nudity or sexual activity',
        'hate': 'Hate speech',
        'bullying': 'Bullying or harassment',
        'suicide': 'Suicide or self-injury',
        'violence': 'Violence or dangerous organizations',
        'spam': 'Spam'
    }
    
    formatted_reasons = ", ".join([reason_map.get(r, str(r)) for r in reasons])
    
    subject = "Notice: Your post has been removed from Vircle"
    message = f"Hello, your recent post has been removed by our moderation team because it received multiple user reports for the following reasons: {formatted_reasons}. Please adhere to our community guidelines."
    
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@vircle.com')
    
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[post.user.email],
            fail_silently=False,
        )
    except Exception as e:
        pass
    
    post.delete()
    return JsonResponse({'status': 'success'})


@login_required(login_url='login')
def post_detail(request, post_id):
    post = get_object_or_404(UserPosts.objects.select_related('user__userprofile'), id=post_id)
    user = request.user
    post.liked_by_user = Like.objects.filter(user=user, post=post).exists()
    post.saved_by_user = UserSavedPosts.objects.filter(user=user, post=post).exists()
    post.is_following = Follower.objects.filter(follower=user, following=post.user).exists()
    post.is_portrait = post.image_height > post.image_width if post.image_height and post.image_width else False

    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        user_profile = None

    notifications = Notification.objects.filter(user=user, read=False).order_by('-timestamp')
    follow_requests = FollowRequest.objects.filter(to_user=user, is_accepted=False)
    total_posts = UserPosts.objects.filter(user=user).count()
    total_followers = Follower.objects.filter(following=user).count()
    total_following = Follower.objects.filter(follower=user).count()

    context = {
        'post': post,
        'user_profile': user_profile,
        'user': user,
        'notifications': notifications,
        'follow_requests': follow_requests,
        'total_posts': total_posts,
        'total_followers': total_followers,
        'total_following': total_following,
    }
    return render(request, 'list_posts/post_detail.html', context)

