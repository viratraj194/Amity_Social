from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from functools import wraps


def owner_required(model_class, lookup_field='id', lookup_url_kwarg=None, redirect_url='list_posts'):
    """
    Decorator to check if the current user owns the object.

    Usage:
        @owner_required(Event, lookup_url_kwarg='event_id')
        def edit_event(request, event_id):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            lookup_value = kwargs.get(lookup_url_kwarg or lookup_field)
            obj = get_object_or_404(model_class, **{lookup_field: lookup_value})

            # Check if user owns the object (assumes eventCreator or user field)
            if hasattr(obj, 'eventCreator'):
                if obj.eventCreator != request.user:
                    messages.error(request, 'You do not have permission to perform this action.')
                    return redirect(redirect_url)
            elif hasattr(obj, 'user'):
                if obj.user != request.user:
                    messages.error(request, 'You do not have permission to perform this action.')
                    return redirect(redirect_url)

            # Store object in kwargs for view to use
            kwargs['object'] = obj
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def self_or_owner_required(redirect_url='list_posts'):
    """
    Decorator to check if the user is accessing their own resource or owns it.
    Checks for user_id in URL kwargs.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            user_id = kwargs.get('user_id')
            if user_id and int(user_id) != request.user.id:
                messages.error(request, 'You can only perform this action on your own profile.')
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def is_following_or_self(redirect_url='list_posts'):
    """
    Decorator to check if the current user follows the target user or is the same user.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            from accounts.models import Follower
            user_id = kwargs.get('user_id')

            if user_id and int(user_id) != request.user.id:
                is_following = Follower.objects.filter(
                    follower=request.user,
                    following_id=user_id
                ).exists()

                if not is_following:
                    messages.error(request, 'You must follow this user to access this content.')
                    return redirect(redirect_url)

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
