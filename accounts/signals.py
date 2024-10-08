from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from . models import User, UserProfile
import redis
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver


@receiver(post_save, sender=User)
def post_save_create_profile_receiver(sender, instance, created, **kwargs):
    
    if created:
        UserProfile.objects.create(user=instance)

    else:
        try:
            profile = UserProfile.objects.get(user=instance)
            profile.save()
        except:
            #create profile whose profile is not exists in database but has updated
            UserProfile.objects.create(user=instance)


# post_save.connect(post_save_create_profile_receiver, sender=User)


@receiver(pre_save, sender=User)
def pre_save_profile_receiver(sender, instance, **kwargs0):
    pass



# @receiver(user_logged_in)
# def handle_user_logged_in(sender, request, user, **kwargs):
#     r = redis.Redis()
#     r.set(f'user:{user.id}:status', 'online')

# @receiver(user_logged_out)
# def handle_user_logged_out(sender, request, user, **kwargs):
#     r = redis.Redis()
#     r.set(f'user:{user.id}:status', 'offline')
