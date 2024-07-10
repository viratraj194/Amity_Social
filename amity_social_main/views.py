from django.shortcuts import render,redirect
from django.shortcuts import HttpResponse
from django.contrib import messages

def home(request):
    if request.user.is_authenticated:
        # messages.warning(request,'you are already logged in.')
        return redirect('list_posts')

    return render(request,'home.html')
