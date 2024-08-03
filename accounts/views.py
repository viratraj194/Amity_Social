from django.shortcuts import render,HttpResponse,redirect,get_object_or_404
from . forms import UserForm,userInfoForm,userProfileForm
from .models import User,UserProfile,Follower,FollowRequest
from . utils import users_id_generator,send_email_verification,detectUser
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.template.defaultfilters import slugify
from list_posts .models import UserPosts,UserSavedPosts,Comment
from list_posts . forms import addCommentForm
from django.http import JsonResponse



   
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
            form.errors
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


def login(request):
    if request.user.is_authenticated:
        messages.warning(request,'you are already logged in.')
        return redirect('list_posts')
    elif request.method =='POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(email=email,password=password)
        if user is not None:
            auth.login(request,user)
            

            messages.success(request,'You are now logged in.')
            return redirect('list_posts')
        else:
            messages.error(request,'Invalid credentials!')
            return redirect('list_posts')
    return render(request,'accounts/login.html')


def logout(request):
    auth.logout(request)
    messages.success(request, 'you have logged out successfully'.title())
    return redirect('login')


    
@login_required(login_url='login')
def account(request):
    user = request.user
    redirectUrl = detectUser(user)
    return redirect(redirectUrl)

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
            user = User.objects.get(pk = pk)
            user.set_password(password)
            user.is_active = True
            user.save()
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
    print(user.collage_name)
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
            print('User Profile Form Errors:', user_profile_form.errors)
            print('User Info Form Errors:', user_info_form.errors)
    else:
        user_profile_form = userProfileForm(instance=user_profile)
        user_info_form = userInfoForm(instance=request.user)
     
    profile = UserProfile.objects.get(user=user)
    print('here is the profile',profile.profile_picture)
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

    total_following = following.count()
    total_followers = followers.count()
    
    
    total_posts =  user_posts.count()
    user_saves = UserSavedPosts.objects.filter(user=request.user)
    total_saved = user_saves.count()
 
    context = {
        'profile':profile,
        'user_posts':user_posts,
        'total_posts':total_posts,
        'total_saved':total_saved,
        'total_following':total_following,
        'total_followers':total_followers,

    }
    return render(request,'accounts/UserDashboard.html',context)

def SavedPosts(request):
    profile = UserProfile.objects.get(user=request.user)
    user_posts = UserPosts.objects.filter(user=request.user)
    saved_posts = UserSavedPosts.objects.filter(user=request.user).order_by('-created_at')
    total_posts =  user_posts.count()
    total_saved = saved_posts.count()

    context = {
        'profile':profile,
        'saved_posts':saved_posts,
        'total_posts':total_posts,
        'total_saved':total_saved
    }
    return render(request,'accounts/SavedPosts.html',context)


def post_details(request,post_slug):
    post = get_object_or_404(UserPosts,post_slug=post_slug)
    comments = Comment.objects.filter(post=post)
    if request.method == 'POST':
        form = addCommentForm(request.POST)
        if form.is_valid():
            new_comment = form.save(commit=False)
            new_comment.post = post
            new_comment.user = request.user
            new_comment.save()
            return redirect('post_details',post_slug=post_slug)
    comment_form = addCommentForm()
    context = {
        'post':post,
        'comments':comments,
        'comment_form':comment_form
        
    }

    return render(request,'accounts/post_details.html',context)


def deletePost(request,post_slug):
    post = get_object_or_404(UserPosts,post_slug = post_slug,user=request.user)
    post.delete()
    return redirect('UserDashboard')


# follow systems 
def send_follow_request(request,user_id):
    to_user = get_object_or_404(User,id=user_id)
    from_user = request.user
    if from_user == to_user:
        messages.error(request,'You can follow yourself!')
        return redirect('list_posts')
    elif FollowRequest.objects.filter(from_user=from_user,to_user=to_user).exists():
        messages.info(request,'Request is already sent!')
        return redirect('profile_details',user_id=user_id)
    else:
        FollowRequest.objects.create(to_user=to_user,from_user=from_user)
        messages.success(request,'Follow request sent.'.title())
        return redirect('profile_details',user_id=user_id)

    return redirect('profile_details',user_id=user_id)

# accepting the request 
def accept_follow_request(request,request_id):
    follow_request = get_object_or_404(FollowRequest, id=request_id, to_user=request.user)
    
    if follow_request:
        # Check if the follower relationship already exists
        existing_follower = Follower.objects.filter(follower=follow_request.from_user, following=follow_request.to_user).exists()
        
        if not existing_follower:
            # Create a new Follower instance if not already following
            Follower.objects.create(follower=follow_request.from_user, following=follow_request.to_user)
            follow_request.is_accepted = True
            follow_request.save()
            return JsonResponse({'status': 'accepted'})
        else:
            # If already following, just mark the follow request as accepted
            follow_request.is_accepted = True
            follow_request.save()
            return JsonResponse({'status': 'already_following'})
    return JsonResponse({'status': 'error'}, status=400)


def deny_follow_request(request,request_id):
    
    follow_request = get_object_or_404(FollowRequest, id=request_id, to_user=request.user)
    if follow_request:
        follow_request.delete()
        return JsonResponse({'status': 'denied'})
    return JsonResponse({'status': 'error'}, status=400)