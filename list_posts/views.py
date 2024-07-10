from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile,User

@login_required(login_url='login')
def list_posts(request):
    user_profile = UserProfile.objects.get(user=request.user)
    user = request.user
    context = {
        'user_profile':user_profile,
        'user':user,

    }

    return render(request,'list_posts/list_posts.html',context)
