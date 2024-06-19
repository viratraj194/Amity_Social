from django import forms
from .models import User


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), min_length=8)
    conform_password = forms.CharField(widget=forms.PasswordInput(),min_length=8)

    class Meta:
        model = User
        fields = ['first_name','last_name','username','email','password','gender','id_card_image','agree_to_terms','id_card_number']


        # def clean(self):
        #     cleaned_data = super().clean()
        #     if not cleaned_data.get('agree_to_terms'):
        #         raise forms.ValidationError('You must agree to the terms and conditions.')
        #     return cleaned_data