import hashlib
import os
import time

from django.utils.text import slugify
from .models import User


def secure_hash_filename(instance, filename):
    """
    Generate a SHA-256 hashed filename for secure uploads.
    """
    ext = os.path.splitext(filename)[1].lower()
    user_id = getattr(getattr(instance, 'user', None), 'id', 0) if instance else 0
    timestamp = str(int(time.time()))
    hash_input = f"{filename}_{user_id}_{timestamp}"
    hash_digest = hashlib.sha256(hash_input.encode()).hexdigest()[:32]
    return f"{hash_digest}{ext}"

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
