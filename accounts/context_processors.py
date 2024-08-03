from . models import UserProfile

def get_user_profile(request):
    try:
        user_profile = UserProfile.objects.get(user= request.user)
    except:
        user_profile = None
    return dict(user_profile=user_profile)