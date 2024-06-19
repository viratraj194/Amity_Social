from django.shortcuts import render,HttpResponse,redirect
from . forms import UserForm
from .models import User
from . utils import users_id_generator

def RegisterUser(request):
    if request.method == 'POST':
        print(request.POST,request.FILES)
        form = UserForm(request.POST,request.FILES)
        if form.is_valid():
            user = form.save()
            user.users_id = users_id_generator(user.id)
            print(user.users_id)
            form.save()
            # user = UserProfile.users_id
            return redirect('home')
        else:
            print(form.errors)

    else:
        form = UserForm()
    form = UserForm()
    
    context = {
        'form':form,
    }

    return render(request,'accounts/RegisterUser.html',context)
