from django import forms
from .models import UserPosts

class addPostsForm(forms.ModelForm):
    class Meta:
        model = UserPosts
        fields = ['content','caption','post_image']