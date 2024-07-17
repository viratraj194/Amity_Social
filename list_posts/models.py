from django.db import models
from accounts.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class UserPosts(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    content = models.TextField(blank=True,null=True)
    caption = models.TextField(max_length=40,blank=True,null=True)

    post_image = models.ImageField(upload_to = 'users/posts/post_image',blank=True, null = True, width_field='image_width', height_field='image_height')   
    image_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    image_height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    
    post_slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"post by {self.user.username}"
    
    # def save(self, *args, **kwargs):
    #     if not self.content and not self.caption and not self.post_image:
    #         raise ValidationError("You cannot post an empty post. Please provide content, caption, or an image.")
    #     super().save(*args, **kwargs)

    
    class Meta:
        verbose_name = 'UserPost'
        verbose_name_plural = 'UserPosts'

        

class Like(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    post = models.ForeignKey(UserPosts,related_name='likes', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')

    def __str__(self):
        return f'{self.user.username} likes {self.post.id}'


# class Comment(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
#     text = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f'Comment by {self.user.username} on {self.post.id}'
    


# test notification 
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    post = models.ForeignKey(UserPosts, on_delete=models.CASCADE, related_name='notifications')
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actor')
    timestamp = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)


    def __str__(self):
        return f"{self.actor} liked {self.user}'s post"