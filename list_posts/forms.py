from django import forms
from .models import UserPosts,Comment
from amity_social_main.validators import validate_image_field

class addPostsForm(forms.ModelForm):
    class Meta:
        model = UserPosts
        fields = ['content','caption','post_image']

    def clean_post_image(self):
        image = self.cleaned_data.get('post_image')
        if image:
            validate_image_field(image)
        return image


class addCommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']