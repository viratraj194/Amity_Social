from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'username', 'is_active', 'is_approved')
    ordering = ('-date_joined',)
    list_editable = ('is_approved',)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
class CustomCollegeAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "is_verified")
    search_fields = ("name", "normalized_name", "city", "state")
    list_filter = ("state", "is_verified")
    ordering = ("name",)
    
admin.site.register(Room)
admin.site.register(Message)
admin.site.register(MessageNotification)
admin.site.register(Follower)
admin.site.register(FollowRequest)
admin.site.register(User, CustomUserAdmin)
admin.site.register(UserProfile)
admin.site.register(College, CustomCollegeAdmin)
