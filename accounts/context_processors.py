from . models import UserProfile

def get_user_profile(request):
    try:
        profile = UserProfile.objects.get(user= request.user)
    except:
        profile = None
    return dict(profile=profile)