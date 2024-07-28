from django.contrib import admin
from .models import UserPosts,Like,Notification,Comment,UserSavedPosts


class CustomUserPostsAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'user_username')  # Custom method to display related field data
    search_fields = ['user__username']
    ordering = ('-created_at',)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'Username' 

class NotificationAdmin(admin.ModelAdmin):
    list_display=('actor','read','user','timestamp')
    ordering = ('-timestamp',)
# admin.site.register(CustomUserPosts)


admin.site.register(UserSavedPosts)
admin.site.register(Comment)

admin.site.register(Notification,NotificationAdmin)
admin.site.register(Like)
admin.site.register(UserPosts,CustomUserPostsAdmin)


