from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from list_posts.models import UserPosts
from . forms import UserForm,userInfoForm,userProfileForm
from .models import *
from . utils import users_id_generator,send_email_verification,detectUser
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.template.defaultfilters import slugify
from list_posts .models import UserPosts,UserSavedPosts,Comment,Like
from list_posts . forms import addCommentForm
from django.http import JsonResponse
from django.db.models import Q
from events.models import Event
from django.core.paginator import Paginator
from django.db.models import Max, F
from django.db.models.functions import Coalesce
from datetime import datetime, timezone
from django.db import transaction
from django_ratelimit.decorators import ratelimit








   
def RegisterUser(request):
    if request.user.is_authenticated:
        messages.warning(request,'you are already logged in.')
        return redirect('account')
    elif request.method == 'POST':
        form = UserForm(request.POST,request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            user.set_password(password)
            user = form.save()
            user_f_name = form.cleaned_data['first_name']
            user_l_name = form.cleaned_data['last_name']
            user_name = f'{user_f_name}{user_l_name}'
            user.user_slug = slugify(user_name)+'_'+str(user.id)
            user.users_id = users_id_generator(user.id)
            form.save()
            # send verification
            mail_subject = 'please activate your account'
            mail_template = 'accounts/email/account_activate.html'
            send_email_verification(request,user,mail_subject,mail_template)
            messages.success(request,'Your account is registered successfully wait for the approval.')

            return redirect('RegisterUser')
        else:
            print(form.errors)
    else:
        form = UserForm()
    context = {
        'form':form,
    }
    return render(request,'accounts/RegisterUser.html',context)



def activate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user =None
    if user is not None and default_token_generator.check_token(user,token):
        user.is_active = True
        user.save()
        messages.success(request,'Your account has been activated.')
        return redirect('account')
    else:
        messages.error(request,'invalid activation link')
        return redirect('account')
    pass

@login_required(login_url='login')
def deactivate_account(request):
    user = request.user
    user.is_online = False
    user.is_active = False
    user.save()
    print(user,'is deactivated')
    auth.logout(request)
    messages.success(request, 'you have logged out successfully'.title())
    return redirect('login')

@ratelimit(key='ip', rate='5/m', block=True, method=['POST'])
def login(request):
    if request.user.is_authenticated:
        messages.warning(request,'you are already logged in.')
        return redirect('list_posts')
    elif request.method =='POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(email=email,password=password)
        if user is not None :
            auth.login(request,user)
            user.is_online = True
            user.save()

            messages.success(request,'You are now logged in.')
            return redirect('list_posts')

        else:
            # print(user.is_active)
            messages.error(request,'Invalid credentials!')
            return redirect('list_posts')
    return render(request,'accounts/login.html')

@login_required(login_url='login')
def logout(request):
    user = request.user
    user.is_online = False
    user.save()
    auth.logout(request)
    messages.success(request, 'you have logged out successfully'.title())
    return redirect('login')


    
@login_required(login_url='login')
def account(request):
    user = request.user
    redirectUrl = detectUser(user)
    return redirect(redirectUrl)

@ratelimit(key='ip', rate='3/h', block=True, method=['POST'])
def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact = email)
            mail_subject = 'please click below to reset your password'.title()
            mail_template = 'accounts/email/reset_password_mail.html'
            send_email_verification(request,user, mail_subject,mail_template)
            messages.success(request,'reset password link has sent to your'.title())
            return redirect('login')
        else:
            messages.error(request,"email doesn't match")
            return redirect('forgot_password')
    return render(request,'accounts/forgot_password.html')


def reset_password_validator(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode() 
        user = User._default_manager.get(pk = uid)
    except(TypeError,OverflowError,ValueError,User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid'] = uid
        messages.success(request,'please reset your password'.title())
        return redirect('reset_password')
    else:
        messages.error(request,"email didn't exist")
        return redirect('account')

def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        conform_password = request.POST['conform_password']
        if password == conform_password:
            pk = request.session.get('uid')
            if not pk:
                messages.error(request, 'Invalid password reset session. Please request a new link.')
                return redirect('forgot_password')
            try:
                user = User.objects.get(pk=pk)
            except User.DoesNotExist:
                messages.error(request, 'Invalid password reset link.')
                return redirect('forgot_password')
            user.set_password(password)
            user.is_active = True
            user.save()
            # Clear the session key after successful reset
            del request.session['uid']
            messages.success(request,'You have updated your password successfully'.title())
            return redirect('login')
        else:
            messages.error(request,"password didn't match".title())
            return redirect('reset_password')
    return render(request,'accounts/reset_password.html')



@login_required(login_url='login')
def userProfileSettings(request):
    # Fetch the user profile
    user_profile = get_object_or_404(UserProfile, user=request.user)
    user = request.user
    # userInfo = get_object_or_404(User,user=user)
   
    if request.method == 'POST':
        user_profile_form = userProfileForm(request.POST, request.FILES, instance=user_profile)
        user_info_form = userInfoForm(request.POST, instance=request.user)
        if user_profile_form.is_valid() and user_info_form.is_valid():
            # Print the cleaned data from the forms
            # Uncomment the following lines to save the data to the database
            user_profile_form.save()
            user_info_form.save()
        else:
            messages.error(request,'Form is invalid')
            
    else:
        user_profile_form = userProfileForm(instance=user_profile)
        user_info_form = userInfoForm(instance=request.user)
     
    profile = UserProfile.objects.get(user=user)
    
    context = {
        'user_profile_form': user_profile_form,
        'user_info_form': user_info_form,
        'saved_collage':user.collage_name,
        'profile':profile,
    }

    return render(request, 'accounts/userProfileSettings.html', context)








@login_required(login_url='login')
def UserDashboard(request):
    profile = UserProfile.objects.get(user=request.user)
    user = request.user
    user_posts = UserPosts.objects.filter(user=user).order_by('-created_at')
    # Get all users who are following the logged-in user
    followers = Follower.objects.filter(following=user).select_related('follower')
    # Get all users the logged-in user is following
    following = Follower.objects.filter(follower=user).select_related('following')
    # list event in hte dashboard
    list_events = Event.objects.filter(eventCreator=user)
    totalEvent = list_events.count()
    total_following = following.count()
    total_followers = followers.count()
    
    
    total_posts =  user_posts.count()
    user_saves = UserSavedPosts.objects.filter(user=request.user)
    total_saved = user_saves.count()


    # infinite scrolling 
    paginator = Paginator(user_posts,8)
    page = int(request.GET.get('page', 1))
    try:
        user_posts = paginator.page(page)
    except:
        return HttpResponse('')
 
    context = {
        'profile':profile,
        'user_posts':user_posts,
        'total_posts':total_posts,
        'total_saved':total_saved,
        'total_following':total_following,
        'total_followers':total_followers,
        'totalEvent':totalEvent,
        'page':page,

    }
    if request.headers.get('HX-Request') == 'true':
        return render(request,'accounts\loop_users_posts.html',context)
    return render(request,'accounts/UserDashboard.html',context)


@login_required(login_url='login')
def SavedPosts(request):
    profile = UserProfile.objects.get(user=request.user)
    user_posts = UserPosts.objects.filter(user=request.user)
    saved_posts = UserSavedPosts.objects.filter(user=request.user).order_by('-created_at')
    total_posts =  user_posts.count()
    total_saved = saved_posts.count()
    user = request.user
    # Get all users who are following the logged-in user
    followers = Follower.objects.filter(following=user).select_related('follower')
    # Get all users the logged-in user is following
    following = Follower.objects.filter(follower=user).select_related('following')
    # list event in hte dashboard
    list_events = Event.objects.filter(eventCreator=user)
    totalEvent = list_events.count()
    total_following = following.count()
    total_followers = followers.count()

    # infinite scrolling 
    paginator = Paginator(saved_posts,8)
    page = int(request.GET.get('page', 1))
    try:
        saved_posts = paginator.page(page)
    except:
        return HttpResponse('')

    context = {
        'profile':profile,
        'saved_posts':saved_posts,
        'total_posts':total_posts,
        'total_saved':total_saved,
        'total_following':total_following,
        'total_followers':total_followers,
        'totalEvent':totalEvent,
        'page':page,
    }
    if request.headers.get('HX-Request') == 'true':
        return render(request,'accounts\loop_saved.html',context)
    return render(request,'accounts/SavedPosts.html',context)

@login_required(login_url='login')
def post_details(request,post_slug):
    post = get_object_or_404(UserPosts,post_slug=post_slug)
    comments = Comment.objects.filter(post=post)
    likes = Like.objects.filter(post=post)
    total_likes = likes.count()
    total_comments = comments.count()
    profile = UserProfile.objects.get(user=request.user)
    user_posts = UserPosts.objects.filter(user=request.user)
    saved_posts = UserSavedPosts.objects.filter(user=request.user).order_by('-created_at')
    total_posts =  user_posts.count()
    total_saved = saved_posts.count()
    user = request.user
    # Get all users who are following the logged-in user
    followers = Follower.objects.filter(following=user).select_related('follower')
    # Get all users the logged-in user is following
    following = Follower.objects.filter(follower=user).select_related('following')
    # list event in hte dashboard
    list_events = Event.objects.filter(eventCreator=user)
    totalEvent = list_events.count()
    total_following = following.count()
    total_followers = followers.count()
    if request.method == 'POST':
        form = addCommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.post = post
            new_comment.user = request.user
            new_comment.save()
            return redirect('post_details',post_slug=post_slug)
    comment_form = addCommentForm()
    liked_by_user = Like.objects.filter(user=user, post=post).exists()
    context = {
        'post':post,
        'comments':comments,
        'comment_form':comment_form,
        'profile':profile,
        'saved_posts':saved_posts,
        'total_posts':total_posts,
        'total_saved':total_saved,
        'total_following':total_following,
        'total_followers':total_followers,
        'totalEvent':totalEvent,
        'total_comments':total_comments,
        'total_likes':total_likes,
        'liked_by_user':liked_by_user,
        
        
    }

    return render(request,'accounts/post_details.html',context)

@login_required(login_url='login')
def post_details_like(request,post_id):
    user = request.user
    post = get_object_or_404(UserPosts,id = post_id)
    if Like.objects.filter(user=user,post=post).exists():
        Like.objects.filter(user=user,post=post).delete()
        liked = False
    else:
        Like.objects.create(user=user,post=post)
        liked = True
        if post.user != user:
            Notification.objects.create(user=post.user,post = post,actor=user, notification_msg='Liked your Post.')

    return redirect('post_details',post_slug=post.post_slug)

def deletePost(request,post_slug):
    post = get_object_or_404(UserPosts,post_slug = post_slug,user=request.user)
    collage_name = post.user.collage_name
    post.delete()
    # Invalidate cache for the college feed
    from django.core.cache import cache
    cache.delete(f'posts_list_{collage_name}_page_1')
    return redirect('UserDashboard')

@login_required(login_url='login')
# follow systems
def send_follow_request(request,user_id):
    to_user = get_object_or_404(User,id=user_id)
    from_user = request.user

    if from_user == to_user:
        messages.error(request,'You can follow yourself!')
        return redirect('list_posts')

    with transaction.atomic():
        # Check if already following
        if Follower.objects.filter(follower=from_user, following=to_user).exists():
            messages.info(request,'You are already following this user.')
            return redirect('profile_details',user_id=user_id)

        # Check if request already exists (use get_or_create for atomicity)
        request_obj, created = FollowRequest.objects.get_or_create(
            from_user=from_user,
            to_user=to_user,
            defaults={'is_accepted': False}
        )

        if created:
            messages.success(request,'Follow request sent.'.title())
        else:
            messages.info(request,'Request is already sent!')

    return redirect('profile_details',user_id=user_id)
@login_required(login_url='login')
# accepting the request
def accept_follow_request(request,request_id):
    follow_request = get_object_or_404(FollowRequest, id=request_id, to_user=request.user)

    with transaction.atomic():
        # Check if the follower relationship already exists
        existing_follower = Follower.objects.filter(follower=follow_request.from_user, following=follow_request.to_user).exists()

        if not existing_follower:
            # Create a new Follower instance if not already following
            Follower.objects.create(follower=follow_request.from_user, following=follow_request.to_user)

        # Always delete the request
        follow_request.delete()
        return JsonResponse({'status': 'accepted' if not existing_follower else 'already_following'})

    return JsonResponse({'status': 'error'}, status=400)
@login_required(login_url='login')
def unFollow(request,user_id):
    profile = get_object_or_404(User,id=user_id)
    Follower.objects.filter(follower=request.user, following=profile).delete()
    messages.success(request,'UnFollowed')
    return redirect('profile_details',user_id=user_id)

def deny_follow_request(request,request_id):
    
    follow_request = get_object_or_404(FollowRequest, id=request_id, to_user=request.user)
    if follow_request:
        follow_request.delete()
        return JsonResponse({'status': 'denied'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required(login_url='login')
def room_chat(request, slug):
    sender = request.user
    # Fetch the room based on the slug
    room = get_object_or_404(Room.objects.prefetch_related('participants__userprofile'), slug=slug)

    # SECURITY: Verify user is a participant in the room
    if not room.participants.filter(id=sender.id).exists():
        messages.error(request, 'You do not have access to this chat room.')
        return redirect('friend_messages')

    # Fetch all messages related to this room, ordered by timestamp - optimized with select_related
    messages = room.messages.select_related('sender__userprofile', 'receiver__userprofile').order_by('created_at')
    # Mark messages as read
    now = datetime.now(timezone.utc)
    room.messages.filter(receiver=sender, status__lt=Message.STATUS_READ).update(status=Message.STATUS_READ, read_at=now)
    # Also mark message notifications as read
    MessageNotification.objects.filter(user=sender, room=room, is_read=False).update(is_read=True)

    receiver = room.participants.exclude(id=sender.id).first()  # For private chats

    # listing all the room user is connected with - optimized query with ordering by last message
    rooms = Room.objects.filter(
        participants=sender
    ).annotate(
        last_message_time=Coalesce(Max('messages__created_at'), F('created_at'))
    ).order_by('-last_message_time').prefetch_related('participants__userprofile')

    rooms_with_photos = []
    for rom in rooms:
        other_participants = [p for p in rom.participants.all() if p.id != sender.id]
        other_user = other_participants[0] if other_participants else None
        if not other_user:
            continue

        last_message = rom.messages.order_by('-created_at').first()
        # Check for unread messages using status field
        unread_msg = rom.messages.filter(receiver=sender, status__lt=Message.STATUS_READ).exists()

        # Check if the other user has a UserProfile and use a default photo if not
        profile_photo_url = getattr(other_user, 'userprofile', None)
        if profile_photo_url and hasattr(profile_photo_url, 'profile_picture') and profile_photo_url.profile_picture:
            profile_photo_url = profile_photo_url.profile_picture.url
        else:
            profile_photo_url = 'static/img/images.jpeg'

        rooms_with_photos.append({
            'room_id': rom.id,
            'room_name': rom.name,
            'room_slug': rom.slug,
            'other_user_id': other_user.id,
            'other_user_name': other_user.username,
            'profile_photo_url': profile_photo_url,
            'last_message_content': last_message.content if last_message else '',
            'last_message_time': last_message.created_at if last_message else None,
            'unread_msg': unread_msg,
        })

    context = {
        'room': room,
        'messages': messages,
        'sender': sender,
        'receiver': receiver,
        'rooms_with_photos': rooms_with_photos,
    }
    return render(request, 'accounts/message.html', context)



@login_required(login_url='login')
def message_user(request, user_id):
    receiver = get_object_or_404(User, id=user_id)
    sender = request.user

    room = Room.objects.filter(
        is_private = True,
        participants = sender
    ).filter(participants=receiver).first()

    if not room:
        room = Room.objects.create(
            is_private=True,
            is_group=False,
            creator=sender,
            
        )
        room.participants.add(sender,receiver)
        room.slug = f"privet-{sender.id}-{receiver.id}"
        room.save()
    return redirect('room_chat',slug = room.slug)


@login_required(login_url='login')
def friend_messages(request):
    user = request.user
    # Optimize: prefetch participants with profiles and order by last message time
    rooms = Room.objects.filter(
        participants=user
    ).annotate(
        last_message_time=Coalesce(Max('messages__created_at'), F('created_at'))
    ).order_by('-last_message_time').prefetch_related('participants__userprofile')

    rooms_with_photos = []
    for room in rooms:
        other_participants = [p for p in room.participants.all() if p.id != user.id]
        other_user = other_participants[0] if other_participants else None
        if not other_user:
            continue

        # Get last message efficiently
        last_message = room.messages.order_by('-created_at').first()
        # Check for unread messages using status field
        unread_msg = room.messages.filter(receiver=user, status__lt=Message.STATUS_READ).exists()

        # Check if the other user has a UserProfile and use a default photo if not
        profile_photo_url = getattr(other_user, 'userprofile', None)
        if profile_photo_url and hasattr(profile_photo_url, 'profile_picture') and profile_photo_url.profile_picture:
            profile_photo_url = profile_photo_url.profile_picture.url
        else:
            profile_photo_url = 'static/img/images.jpeg'

        rooms_with_photos.append({
            'room': room,
            'other_user': other_user,
            'profile_photo': profile_photo_url,
            'last_message': last_message,
            'unread_msg': unread_msg,
        })

    context = {
        'rooms_with_photos': rooms_with_photos,
    }
    return render(request, 'accounts/friend_messages.html', context)


# Create a Redis instance
from django.http import JsonResponse
import redis
from decouple import config

redis_instance = redis.StrictRedis(
    host=config('REDIS_HOST', default='127.0.0.1'),
    port=config('REDIS_PORT', default='6379', cast=int),
    db=0,
    password=config('REDIS_PASSWORD', default=None)
)

def get_user_status(request, user_id):
    try:
        r = redis.Redis(
            host=config('REDIS_HOST', default='127.0.0.1'),
            port=config('REDIS_PORT', default='6379', cast=int),
            password=config('REDIS_PASSWORD', default=None)
        )
        status = r.get(f'user:{user_id}:status')
        if status:
            return JsonResponse({'status': status.decode('utf-8')})
        else:
            return JsonResponse({'status': 'offline'})
    except Exception as e:
        return JsonResponse({'status': 'offline'})



@login_required(login_url='login')
def followers(request):
    if request.method == 'GET':
        user_id = request.user.id

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        followers = Follower.objects.filter(following=user).select_related('follower')
       

        followers_list = [{'id': follower.follower.id, 'username': follower.follower.username,'profile_picture': follower.follower.userprofile.profile_picture.url,'first_name': follower.follower.first_name,'last_name': follower.follower.last_name} for follower in followers]

        return JsonResponse({'followers': followers_list}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)
@login_required(login_url='login')
def following(request):
    if request.method == 'GET':
        user_id = request.user.id

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)

        followings = Follower.objects.filter(follower=user).select_related('following')

        followers_list = [{'id': following.following.id, 'username': following.following.username,
                           'profile_picture': following.following.userprofile.profile_picture.url,
                           'first_name': following.following.first_name, 'last_name': following.following.last_name}
                          for following in followings]

        return JsonResponse({'followers': followers_list}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)

    # Get all users the logged-in user is following
    # following = Follower.objects.filter(follower=user).select_related('following')


import requests
from django.http import JsonResponse

def get_colleges(request):
    # New API endpoint (raw JSON file on GitHub)
    api_url = "https://raw.githubusercontent.com/Hipo/university-domains-list/master/world_universities_and_domains.json"

    try:
        response = requests.get(api_url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            # Filter only Indian colleges
            indian_colleges = [college for college in data if college.get("country", "").lower() == "india"]
            return JsonResponse(indian_colleges, safe=False)

        return JsonResponse({"error": "Failed to fetch data", "status": response.status_code}, status=500)

    except requests.exceptions.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
