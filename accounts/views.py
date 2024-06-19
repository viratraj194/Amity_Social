from django.shortcuts import render,HttpResponse,redirect
from . forms import UserForm
from .models import User
from . utils import users_id_generator

def RegisterUser(request):
    if request.method == 'POST':
        form = UserForm(request.POST,request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            user.set_password(password)
            user.users_id = users_id_generator(user.id)
            form.save()
            # user = UserProfile.users_id
            return redirect('RegisterUser')
        else:
            print(form.errors)
            form.errors


    else:
        form = UserForm()    
    context = {
        'form':form,
    }

    return render(request,'accounts/RegisterUser.html',context)
