from django.shortcuts import render,HttpResponse,redirect
from . forms import UserForm

def RegisterUser(request):
    if request.method == 'POST':
        print(request.POST,request.FILES)
        form = UserForm(request.POST,request.FILES)
        if form.is_valid():
            user = form.save()
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
