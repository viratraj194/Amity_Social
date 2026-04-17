from django.db import models
from accounts.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone

class UserPosts(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,db_index=True)
    content = models.TextField(blank=True,null=True)
    caption = models.TextField(max_length=200,blank=True,null=True)

    post_image = models.ImageField(upload_to = 'users/posts/post_image',blank=True, null = True, width_field='image_width', height_field='image_height')   
    image_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    image_height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    
    post_slug = models.SlugField(unique=True,db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"post by {self.user.username}"
    
    def total_likes(self):
        return self.likes.count()

    def total_comments(self):
        return self.comments.count()
    
    # def save(self, *args, **kwargs):
    #     if not self.content and not self.caption and not self.post_image:
    #         raise ValidationError("You cannot post an empty post. Please provide content, caption, or an image.")
    #     super().save(*args, **kwargs)

    
    class Meta:
        verbose_name = 'UserPost'
        verbose_name_plural = 'UserPosts'

        

        

class Like(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, db_index=True)
    post = models.ForeignKey(UserPosts,related_name='likes', on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'post')
        indexes = [
            models.Index(fields=['user', 'post']),
            models.Index(fields=['post']),
        ]

    def __str__(self):
        return f'{self.user.username} likes {self.post.id}'


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(UserPosts, related_name='comments', on_delete=models.CASCADE)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies', db_index=True)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', '-created_at']),
            models.Index(fields=['parent']),
        ]

    def __str__(self):
        if self.parent:
            return f'Reply by {self.user.username} on {self.post.id}'
        return f'Comment by {self.user.username} on {self.post.id}'

    @property
    def is_reply(self):
        return self.parent is not None

    def reply_count(self):
        return self.replies.count()
    


# test notification 
class Notification(models.Model):
    # notification_title = models.CharField(blank=True,null=True,db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', db_index=True)
    post = models.ForeignKey(UserPosts, on_delete=models.CASCADE, related_name='notifications', db_index=True)
    notification_msg = models.CharField(blank=True,null=True)
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actor', db_index=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    read = models.BooleanField(default=False, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'read']),
            models.Index(fields=['user', '-timestamp']),
        ]

    def __str__(self):
        return f"{self.actor} Notified {self.user}'s post"


class UserSavedPosts(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE, db_index=True)
    post = models.ForeignKey(UserPosts,on_delete=models.CASCADE,related_name='saved_posts', db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['post']),
            models.Index(fields=['user', 'post']),
        ]
        unique_together = ('user', 'post')
        verbose_name = 'User Saved Post'
        verbose_name_plural = 'User Saved Posts'

    def __str__(self):
        return f"{self.user.email} saved {self.post.id}"
