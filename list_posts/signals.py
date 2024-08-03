from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import UserPosts

@receiver(post_save, sender=UserPosts)
@receiver(post_delete, sender=UserPosts)
def clear_post_cache(sender, **kwargs):
    cache.delete('list_posts')
    print('post has been updated')