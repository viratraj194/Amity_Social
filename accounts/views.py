from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from list_posts.models import UserPosts,Notification
from . forms import UserForm,userInfoForm,userProfileForm,INDIA_REGIONS
from .models import *
from . utils import users_id_generator,send_email_verification,detectUser,get_or_create_college
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
from django.core.cache import cache








   
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

            # Handle state and city from form
            state = form.cleaned_data.get('state')
            city = form.cleaned_data.get('city')
            # Get college_name from visible input or hidden backup field
            college_name = request.POST.get('college_name', '').strip() or request.POST.get('college_name_hidden', '').strip()

            # DEBUG: Log what we received
            print(f"DEBUG POST data: college_name='{college_name}', state='{state}', city='{city}'")
            print(f"DEBUG raw POST: college_name={request.POST.get('college_name')}, college_name_hidden={request.POST.get('college_name_hidden')}")

            if state:
                user.state = state
                request.session['user_state'] = state
            if city:
                user.city = city
                request.session['user_city'] = city

            # Handle college: get or create based on name, city, state
            if college_name and state and city:
                college = get_or_create_college(college_name, city=city, state=state)
                if college:
                    user.college = college
                    print(f"REGISTRATION: college assigned - {college.name}")
                else:
                    print(f"REGISTRATION: college is None - name='{college_name}', state='{state}', city='{city}'")

            # Generate users_id BEFORE saving (required field - cannot be empty)
            # Use a temporary ID based on timestamp, will update after save
            import datetime
            temp_id = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
            user.users_id = temp_id

            # First save to get the actual user.id
            user.save()

            # Now update with proper users_id and user_slug
            user_f_name = form.cleaned_data['first_name']
            user_l_name = form.cleaned_data['last_name']
            user_name = f'{user_f_name}{user_l_name}'
            user.users_id = users_id_generator(user.id)
            user.user_slug = slugify(user_name)+'_'+str(user.id)
            user.save()

            # send verification
            mail_subject = 'please activate your account'
            mail_template = 'accounts/email/account_activate.html'
            send_email_verification(request,user,mail_subject,mail_template)
            messages.success(request,'Your account is registered successfully. Check your email(or spam) and activate your account.')

            return redirect('RegisterUser')
        else:
            print(form.errors)
    else:
        form = UserForm()

    context = {
        'form':form,
        'india_regions': INDIA_REGIONS,
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

@ratelimit(key='ip', rate='5/h', block=True, method=['POST'])
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
    user_profile = get_object_or_404(UserProfile, user=request.user)
    user = request.user

    # Initialize variables for context (available for both GET and POST)
    user_city = user.city or ''
    user_state = user.state or ''
    if user.college:
        if not user_state:
            user_state = user.college.state or ''
        if not user_city:
            user_city = user.college.city or ''

    if request.method == 'POST':
        user_profile_form = userProfileForm(request.POST, request.FILES, instance=user_profile)
        user_info_form = userInfoForm(request.POST, instance=request.user)

        if user_profile_form.is_valid() and user_info_form.is_valid():
            # Save profile form first
            user_profile_form.save()

            # Store old college_id for cache invalidation
            old_college_id = user.college.id if user.college else None

            # Handle state and city from form
            state = user_info_form.cleaned_data.get('state')
            city = user_info_form.cleaned_data.get('city')
            # Get college_name from visible input or hidden backup field
            college_name = request.POST.get('college_name', '').strip() or request.POST.get('college_name_hidden', '').strip()

            if state:
                user.state = state
            if city:
                user.city = city

            # Handle college: get or create based on name, city, state
            new_college_id = None
            if college_name and state and city:
                college = get_or_create_college(college_name, city=city, state=state)
                if college:
                    user.college = college
                    new_college_id = college.id
                else:
                    # Fallback: try to find college by exact name match
                    college = College.objects.filter(name__iexact=college_name.strip()).first()
                    if college:
                        user.college = college
                        new_college_id = college.id

            # Save other user fields
            user.first_name = user_info_form.cleaned_data['first_name']
            user.last_name = user_info_form.cleaned_data['last_name']
            user.username = user_info_form.cleaned_data['username']
            user.phone_number = user_info_form.cleaned_data['phone_number']
            user.save()

            # Invalidate cache for old and new college feed
            if old_college_id is not None:
                cache.delete(f'posts_list_{request.user.id}_{old_college_id}_page_1')
            if new_college_id is not None:
                cache.delete(f'posts_list_{request.user.id}_{new_college_id}_page_1')

            messages.success(request, 'Profile updated successfully.')
        else:
            messages.error(request, 'Form is invalid')
            print("Profile form errors:", user_profile_form.errors)
            print("User info form errors:", user_info_form.errors)
    else:
        user_profile_form = userProfileForm(instance=user_profile)
        user_info_form = userInfoForm(instance=request.user)

    profile = UserProfile.objects.get(user=user)

    context = {
        'user_profile_form': user_profile_form,
        'user_info_form': user_info_form,
        'profile': profile,
        'india_regions': INDIA_REGIONS,
        'user_city': user_city,
        'user_state': user_state,
        'user_college_name': user.college.name if user.college else '',
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
        return render(request,'accounts/loop_users_posts.html',context)
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
        return render(request,'accounts/loop_saved.html',context)
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
        # Only create notification if one doesn't already exist
        if post.user != user and not Notification.objects.filter(user=post.user, post=post, actor=user, notification_msg='Liked your Post.').exists():
            Notification.objects.create(user=post.user,post = post,actor=user, notification_msg='Liked your Post.')

    return redirect('post_details',post_slug=post.post_slug)

def deletePost(request,post_slug):
    post = get_object_or_404(UserPosts,post_slug = post_slug,user=request.user)
    college_id = post.user.college.id if post.user.college else None
    post.delete()
    # Invalidate cache for the college feed
    from django.core.cache import cache
    cache.delete(f'posts_list_{post.user.id}_{college_id}_page_1')
    return redirect('UserDashboard')

@login_required(login_url='login')
@ratelimit(key='user', rate='10/m', block=True, method=['POST'])
def send_follow_request(request,user_id):
    to_user = get_object_or_404(User,id=user_id)
    from_user = request.user

    if from_user == to_user:
        messages.error(request,'You cant follow yourself!')
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
    # Handle missing request gracefully instead of 404
    follow_request = FollowRequest.objects.filter(id=request_id, to_user=request.user).first()

    if not follow_request:
        return JsonResponse({'status': 'already_handled', 'message': 'Request not found or already processed'})

    # Get to_user's college_id for cache invalidation before deleting
    to_user_college_id = follow_request.to_user.college.id if follow_request.to_user.college else None

    with transaction.atomic():
        # Check if the follower relationship already exists
        existing_follower = Follower.objects.filter(follower=follow_request.from_user, following=follow_request.to_user).exists()

        if not existing_follower:
            # Create a new Follower instance if not already following
            Follower.objects.create(follower=follow_request.from_user, following=follow_request.to_user)

            Notification.objects.create(
            user=follow_request.from_user,   # 🔥 sender gets notification
            actor=request.user,              # 🔥 who accepted
            notification_msg=f"{request.user.username} accepted your follow request"
        )
        # Always delete the request
        follow_request.delete()

    # Invalidate cache for the to_user to remove stale follow request notification
    if to_user_college_id:
        cache.delete(f'posts_list_{follow_request.to_user.id}_{to_user_college_id}_page_1')

    return JsonResponse({'status': 'accepted' if not existing_follower else 'already_following'})
@login_required(login_url='login')
def unFollow(request,user_id):
    profile = get_object_or_404(User,id=user_id)
    Follower.objects.filter(follower=request.user, following=profile).delete()
    messages.success(request,'UnFollowed')
    return redirect('profile_details',user_id=user_id)

def deny_follow_request(request,request_id):
    # Handle missing request gracefully instead of 404
    follow_request = FollowRequest.objects.filter(id=request_id, to_user=request.user).first()

    if not follow_request:
        return JsonResponse({'status': 'already_handled', 'message': 'Request not found or already processed'})

    # Get to_user's college_id for cache invalidation before deleting
    to_user_college_id = follow_request.to_user.college.id if follow_request.to_user.college else None

    follow_request.delete()

    # Invalidate cache for the to_user to remove stale follow request notification
    if to_user_college_id:
        cache.delete(f'posts_list_{follow_request.to_user.id}_{to_user_college_id}_page_1')

    return JsonResponse({'status': 'denied'})


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


from django.http import JsonResponse

def get_colleges(request):
    """
    Returns all colleges from the local College model with id and name.
    Used for populating the datalist in registration forms.
    """
    colleges = list(College.objects.values('id', 'name').order_by('name'))
    return JsonResponse(colleges, safe=False)


def get_cities(request):
    """
    Returns distinct cities filtered by state from College model.
    Used for populating city dropdown after state selection.
    """
    state = request.GET.get('state', '').strip()

    if not state:
        return JsonResponse([], safe=False)

    # SECURITY: Validate state against known Indian states/UTs
    from .utils import validate_indian_state
    is_valid, normalized_state = validate_indian_state(state)
    if not is_valid:
        return JsonResponse([], safe=False)

    # Get distinct cities for the given state (use validated state)
    cities = College.objects.filter(
        state=normalized_state
    ).values_list('city', flat=True).distinct().order_by('city')

    # Filter out None/empty values and convert to list
    cities_list = [city for city in cities if city]

    return JsonResponse(cities_list, safe=False)

def search_colleges(request):
    """
    Optimized college search API using database with caching.
    NO LOGIN REQUIRED - accessible on registration page.

    Filters by state and city before searching college name.

    Performance optimizations:
    - Short-circuit for empty/short queries
    - Database index on name, state, city fields
    - Query-level caching (5 minutes)
    - LIMIT 10 to reduce payload
    """
    query = request.GET.get('q', '').strip()
    state = request.GET.get('state', '').strip()
    city = request.GET.get('city', '').strip()

    # Short-circuit: require minimum 2 chars for search
    if len(query) < 2:
        return JsonResponse([], safe=False)

    # SECURITY: Validate state if provided
    if state:
        from .utils import validate_indian_state
        is_valid, normalized_state = validate_indian_state(state)
        if not is_valid:
            return JsonResponse([], safe=False)
        state = normalized_state

    # Normalize query for case-insensitive search
    query_lower = query.lower()

    # Build cache key including state and city for proper invalidation
    cache_key = f"college_search_{query_lower}_{state}_{city}"

    # Try cache first (5 minute TTL)
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return JsonResponse(cached_result, safe=False)

    # Build filter dynamically
    filters = Q(name__icontains=query)

    if state:
        filters &= Q(state=state)
    if city:
        filters &= Q(city=city)

    # Optimized DB query using indexed fields
    colleges_qs = College.objects.filter(filters).values('name', 'city', 'state')[:10]

    # Convert queryset to list
    results = list(colleges_qs)

    # Cache the results for 5 minutes
    cache.set(cache_key, results, 300)

    return JsonResponse(results, safe=False)
