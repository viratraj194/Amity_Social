from django import forms
from .models import *


class addEventsForm(forms.ModelForm):
    
    class Meta:
        model = Event
        fields = ['title','description','location','start_datetime','end_datetime','organizer','image','attendees']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-2 mt-2 text-gray-700 bg-transparent border border-gray-300 rounded-md dark:text-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring'
            }),
            'description': forms.Textarea(attrs={
                'class': 'block w-full px-4 py-2 mt-2 text-gray-700 bg-transparent border border-gray-300 rounded-md dark:text-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring'
            }),
            'location': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-2 mt-2 text-gray-700 bg-transparent border border-gray-300 rounded-md dark:text-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring'
            }),
            'start_datetime': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'block w-full px-4 py-2 mt-2 text-gray-700 bg-transparent border border-gray-300 rounded-md dark:text-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring'
            }),
            'end_datetime': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'block w-full px-4 py-2 mt-2 text-gray-700 bg-transparent border border-gray-300 rounded-md dark:text-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring'
            }),
            'organizer': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-2 mt-2 text-gray-700 bg-transparent border border-gray-300 rounded-md dark:text-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring'
            }),
            'attendees': forms.TextInput(attrs={
                'class': 'block w-full px-4 py-2 mt-2 text-gray-700 bg-transparent border border-gray-300 rounded-md dark:text-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'block w-full px-4 py-2 mt-2 text-gray-700 bg-transparent border border-gray-300 rounded-md dark:text-gray-300 dark:border-gray-600 focus:border-blue-500 dark:focus:border-blue-500 focus:outline-none focus:ring'
            }),
        }