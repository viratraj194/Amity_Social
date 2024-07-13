from django.shortcuts import render,redirect
from django.contrib.auth.decorators import login_required
from accounts.models import UserProfile,User
from .forms import addPostsForm
from django.contrib import messages
from django.template.defaultfilters import slugify


@login_required(login_url='login')
def list_posts(request):
    user_profile = UserProfile.objects.get(user=request.user)
    user = request.user
    context = {
        'user_profile':user_profile,
        'user':user,

    }

    return render(request,'list_posts/list_posts.html',context)


def add_posts(request):
    if request.method == 'POST':
        post_form = addPostsForm(request.POST, request.FILES)
        if post_form.is_valid():
            post = post_form.save(commit=False)  # Don't save to the database yet
            post.user = request.user  # Set the user to the current logged-in user
            post.save()  # Save the post now

            # Set post_slug based on user's name and post id
            user = request.user
            user_name = f'{user.first_name}{user.last_name}'
            post.post_slug = slugify(user_name) + '_' + str(post.id)
            post.save()  # Save the post again to update post_slug

            messages.success(request, 'New post is added.')
            return redirect('list_posts')
        else:
            print(post_form.errors)
    else:
        post_form = addPostsForm()
    
    context = {
        'post_form': post_form
    }
    return render(request, 'list_posts/list_posts.html', context)

