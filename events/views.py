from django.shortcuts import render,redirect
from .models import*
from . forms import addEventsForm
import datetime
from django.utils import timezone

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
    context = {
        'allEvents':allEvents,
        'events_this_week': events_this_week,
        'events_this_month': events_this_month,
    }
    return render(request,'events/allEvents.html',context)

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