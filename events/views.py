from django.shortcuts import render,redirect,get_object_or_404,HttpResponse
from .models import*
from . forms import addEventsForm
import datetime
from django.utils import timezone
from accounts.models import*
from list_posts.models import*
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

def get_current_week():
    today = timezone.now()
    start_of_week = today - datetime.timedelta(days=today.weekday())  # Monday
    end_of_week = start_of_week + datetime.timedelta(days=6)  # Sunday
    return start_of_week, end_of_week

def get_current_month():
    today = timezone.now()
    start_of_month = today.replace(day=1)
    next_month = today.replace(day=28) + datetime.timedelta(days=4)  # this will never fail
    end_of_month = next_month - datetime.timedelta(days=next_month.day)
    return start_of_month, end_of_month

@login_required(login_url='login')
def allEvents(request):
     # Get the date ranges
    start_of_week, end_of_week = get_current_week()
    start_of_month, end_of_month = get_current_month()

    # Filter events for the current week
    events_this_week = Event.objects.filter(
        start_datetime__gte=start_of_week,
        start_datetime__lte=end_of_week
    )

    # Filter events for the current month
    events_this_month = Event.objects.filter(
        start_datetime__gte=start_of_month,
        start_datetime__lte=end_of_month
    )
    allEvents = Event.objects.all()
    paginator = Paginator(allEvents,6)
    page = int(request.GET.get('page',1))
    try:
        allEvents = paginator.page(page)
    except:
        return HttpResponse('')
    context = {
        'allEvents':allEvents,
        'events_this_week': events_this_week,
        'events_this_month': events_this_month,
        'page':page,
    }
    if request.headers.get('HX-Request') == 'true':
        return render(request,'events\loop_events.html',context)
    return render(request,'events/allEvents.html',context)
@login_required(login_url='login')
def addEvents(request):
    if request.method == 'POST':
        form = addEventsForm(request.POST,request.FILES)
        if form.is_valid():
            event = form.save(commit=False)  # Create an Event instance but don't save yet
            event.eventCreator = request.user  # Assign the current logged-in user as the eventCreator
            event.save()  # Save the Event instance
            return redirect('allEvents')  # Replace 'event_list' with the URL name you want to redirect to after form submission
        else:
            print(form.errors)
    else:
        form = addEventsForm()

    context = {
        'form': form
    }
    return render(request, 'events/addEvents.html', context)

@login_required(login_url='login')
def userEvents(request):
    events = Event.objects.filter(eventCreator=request.user)
    profile = UserProfile.objects.get(user=request.user)
    user_posts = UserPosts.objects.filter(user=request.user)
    saved_posts = UserSavedPosts.objects.filter(user=request.user)
    total_posts =  user_posts.count()
    total_saved = saved_posts.count()
    total_events = events.count()


    user = request.user
    # Get all users who are following the logged-in user
    followers = Follower.objects.filter(following=user).select_related('follower')
    # Get all users the logged-in user is following
    following = Follower.objects.filter(follower=user).select_related('following')
    # list event in hte dashboard

    total_following = following.count()
    total_followers = followers.count()

    paginator = Paginator(events,4)
    page = int(request.GET.get('page',1))
    try:
        events = paginator.page(page)
    except:
        return HttpResponse('')
    context = {
        'events':events,
        'profile':profile,
        'total_posts':total_posts,
        'total_saved':total_saved,
        'total_events':total_events,
        'total_following':total_following,
        'total_followers':total_followers,
        'page':page,

    }
    if request.headers.get('HX-Request') == 'true':
        return render(request,'events\loopUserEvents.html',context)
    return render(request,'events/userEvents.html',context)
@login_required(login_url='login')
def eventDetails(request,event_id):
    start_of_month, end_of_month = get_current_month()
    event = Event.objects.get(id = event_id)
    
    # Filter events for the current month
    events_this_month = Event.objects.filter(
        start_datetime__gte=start_of_month,
        start_datetime__lte=end_of_month
    )
    
    
    context = {
        'event':event,
        'events_this_month':events_this_month,
    }
    return render(request,'events/eventDetails.html',context)

@login_required(login_url='login')
def editEvent(request,event_id=None):
    event = get_object_or_404(Event,id=event_id)
    if request.method == 'POST':
        form = addEventsForm(request.POST,request.FILES,instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            event.eventCreator = request.user
            event.save()
            messages.success(request,'Event is updated successfully')
            return redirect('account')
        else:
            print(form.errors)
    else:
        form = addEventsForm(instance=event)

    context = {
        'event':event,
        'form':form,
    }

    return render(request,'events/editEvent.html',context)
@login_required(login_url='login')
def deleteEvent(request,event_id):
    event = get_object_or_404(Event,id=event_id)
    event.delete()
    messages.success(request,'Event is deleted successfully')
    return redirect('account')