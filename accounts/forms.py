from django import forms
from django.utils.text import slugify
from .models import User,UserProfile,FollowRequest,College


# Indian States and Union Territories
INDIA_REGIONS = [
    # States (28)
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
    # Union Territories (8)
    ('Andaman and Nicobar Islands', 'Andaman and Nicobar Islands'),
    ('Chandigarh', 'Chandigarh'),
    ('Dadra and Nagar Haveli and Daman and Diu', 'Dadra and Nagar Haveli and Daman and Diu'),
    ('Delhi', 'Delhi'),
    ('Jammu and Kashmir', 'Jammu and Kashmir'),
    ('Ladakh', 'Ladakh'),
    ('Lakshadweep', 'Lakshadweep'),
    ('Puducherry', 'Puducherry'),
]


class UserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), min_length=8)
    conform_password = forms.CharField(widget=forms.PasswordInput(),min_length=8)
    agree_to_terms = forms.BooleanField(required=True, error_messages={'required': 'You must agree to the terms and conditions.'})
    # State field with choices from INDIA_REGIONS
    state = forms.ChoiceField(
        required=True,
        choices=[('', 'Select State / UT')] + INDIA_REGIONS,
        widget=forms.Select(attrs={
            'class': 'state-select',
            'id': 'id_state',
        })
    )
    # City field - populated dynamically based on state selection
    city = forms.CharField(
        required=True,
        widget=forms.Select(attrs={
            'class': 'city-select',
            'id': 'id_city',
            'disabled': 'disabled',  # Initially disabled until state is selected
        })
    )

    class Meta:
        model = User
        fields = ['first_name','last_name','username','email','password','state','city','gender','agree_to_terms']

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('agree_to_terms'):
            raise forms.ValidationError('You must agree to the terms and conditions.')
        password = cleaned_data.get("password")
        conform_password = cleaned_data.get("conform_password")
        if password and conform_password and password != conform_password:
            self.add_error('conform_password', "Passwords do not match")
        return cleaned_data


class userProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(widget=forms.FileInput(attrs={'class': 'btn btn-info'}))
    cover_photo = forms.ImageField(widget=forms.FileInput(attrs={'class': 'btn btn-info'}))
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
    # State field with choices from INDIA_REGIONS
    state = forms.ChoiceField(
        required=True,
        choices=[('', 'Select State / UT')] + INDIA_REGIONS,
        widget=forms.Select(attrs={
            'id': 'id_state',
            'class': 'state-select',
        })
    )
    # City field - populated dynamically based on state selection
    city = forms.CharField(
        required=True,
        widget=forms.Select(attrs={
            'class': 'city-select',
            'id': 'id_city',
            'disabled': 'disabled',  # Initially disabled until state is selected
        })
    )

    class Meta:
        model = User
        fields = ['first_name','last_name','username','phone_number','state','city']

# follow system 

class FollowRequestForm(forms.ModelForm):
    class Meta:
        model = FollowRequest
        fields = ['to_user']