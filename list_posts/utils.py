from django.utils.text import slugify
from .models import User

def generate_unique_slug(instance, new_slug=None):
    if new_slug is not None:
        slug = new_slug
    else:
        slug = slugify(f'{instance.first_name}{instance.users_id}')
    
    Klass = instance.__class__
    if Klass.objects.filter(user_slug=slug).exists():
        new_slug = f"{slug}-{Klass.objects.latest('id').id + 1}"
        return generate_unique_slug(instance, new_slug=new_slug)
    return slug
