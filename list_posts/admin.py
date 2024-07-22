from django.contrib import admin
from .models import UserPosts,Like,Notification,Comment,UserSavedPosts


class CustomUserPostsAdmin(admin.ModelAdmin):
    list_display = ('user','created_at',)
    ordering = ('-created_at',)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()


class NotificationAdmin(admin.ModelAdmin):
    list_display=('actor','read','user','timestamp')
    ordering = ('-timestamp',)
# admin.site.register(CustomUserPosts)


admin.site.register(UserSavedPosts)
admin.site.register(Comment)

admin.site.register(Notification,NotificationAdmin)
admin.site.register(Like)
admin.site.register(UserPosts,CustomUserPostsAdmin)


