from django.db import models
from accounts.models import User


class UserPosts(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    content = models.TextField()
    caption = models.TextField()
    post_image = models.ImageField(upload_to = 'users/posts/post_image',blank=True, null = True)   
    post_video = models.FileField(upload_to='user/posts/post_video', blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"post by {self.user.username}"

        

# class Like(models.Model):
#     user = models.ForeignKey(User,on_delete=models.CASCADE)
#     post = models.ForeignKey(UserPosts,related_name='likes', on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         unique_together = ('user', 'post')

#     def __str__(self):
#         return f'{self.user.username} likes {self.post.id}'


# class Comment(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
#     text = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f'Comment by {self.user.username} on {self.post.id}'
    
