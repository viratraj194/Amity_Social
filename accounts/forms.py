from django import forms
from .models import User,UserProfile


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), min_length=8)
    conform_password = forms.CharField(widget=forms.PasswordInput(),min_length=8)
    agree_to_terms = forms.BooleanField(required=True, error_messages={'required': 'You must agree to the terms and conditions.'})

    class Meta:
        model = User
        fields = ['first_name','last_name','username','email','password','gender','id_card_image','agree_to_terms','id_card_number']


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

    class Meta:
        model = UserProfile
        fields = ['profile_picture','cover_photo','collage_name','collage_pin_code']




class userInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name','last_name','username','phone_number']
