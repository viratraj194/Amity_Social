from django import forms
from .models import User,UserProfile,FollowRequest


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), min_length=8)
    conform_password = forms.CharField(widget=forms.PasswordInput(),min_length=8)
    agree_to_terms = forms.BooleanField(required=True, error_messages={'required': 'You must agree to the terms and conditions.'})

    class Meta:
        model = User
        fields = ['first_name','last_name','username','email','password','collage_name','gender','agree_to_terms']


    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('agree_to_terms'):
            raise forms.ValidationError('You must agree to the terms and conditions.')
        return cleaned_data

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        conform_password = cleaned_data.get("conform_password")
        if password and conform_password and password != conform_password:
            self.add_error('conform_password', "Passwords do not match")
        return cleaned_data


class userProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(widget=forms.FileInput(attrs={'class': 'btn btn-info'}))
    cover_photo = forms.ImageField(widget=forms.FileInput(attrs={'class': 'btn btn-info'}))
    collage_name = forms.CharField(widget=forms.HiddenInput()) 
    # userBio = forms.Textarea(widget=forms.Textarea(attrs={'class': 'block w-full px-4 py-2 mt-2 text-gray-700 bg-transparent border border-gray-300 rounded-md dark:text-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring'}))
    class Meta:
        model = UserProfile
        fields = ['profile_picture','cover_photo','collage_pin_code','userBio','is_privet']
        widgets = {
             'userBio': forms.Textarea(attrs={
                'class': ''
            }),
            'is_private': forms.CheckboxInput(attrs={'class': 'toggle-button form-check-input'}),
           }



class userInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','username','phone_number','collage_name']

# follow system 

class FollowRequestForm(forms.ModelForm):
    class Meta:
        model = FollowRequest
        fields = ['to_user']