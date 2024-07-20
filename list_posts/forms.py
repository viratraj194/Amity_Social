from django import forms
from .models import UserPosts,Comment

class addPostsForm(forms.ModelForm):
    class Meta:
        model = UserPosts
        fields = ['content','caption','post_image']


class addCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']