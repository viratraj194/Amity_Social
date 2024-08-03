from django.contrib import admin
from .models import User, UserProfile,FollowRequest,Follower
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'is_active', 'is_approved')
    ordering = ('-date_joined',)
    list_editable = ('is_approved',)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


admin.site.register(Follower)
admin.site.register(FollowRequest)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
