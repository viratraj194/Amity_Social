from django.shortcuts import render,HttpResponse,redirect
from . forms import UserForm
from .models import User
from . utils import users_id_generator
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required

def RegisterUser(request):
    if request.user.is_authenticated:
        messages.warning(request,'you are already logged in.')
        return redirect('account')
    elif request.method == 'POST':
        form = UserForm(request.POST,request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data['password']
            user.set_password(password)
            user = form.save()
            user.users_id = users_id_generator(user.id)
            form.save()
            messages.success(request,'Your account is registered successfully wait for the approval.')

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


def login(request):
    if request.user.is_authenticated:
        messages.warning(request,'you are already logged in.')
        return redirect('account')
    elif request.method =='POST':
        email = request.POST['email']
        password = request.POST['password']
        user = auth.authenticate(email=email,password=password)

        if user is not None:
            auth.login(request,user)
            messages.success(request,'You are now logged in.')
            return redirect('account')
        else:
            messages.error(request,'Invalid credentials!')
            return redirect('login')
    return render(request,'accounts/login.html')


def logout(request):
    auth.logout(request)
    messages.success(request, 'you have logged out successfully'.title())
    return redirect('login')

@login_required(login_url='login')
def account(request):
    return render(request,'accounts/account.html')
    pass