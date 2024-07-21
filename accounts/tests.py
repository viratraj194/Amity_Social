from django.test import TestCase

# Create your tests here.


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
