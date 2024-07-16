from django.contrib import admin
from .models import UserPosts,Like


class CustomUserPostsAdmin(admin.ModelAdmin):
    list_display = ('user','created_at',)
    ordering = ('-created_at',)
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()

# admin.site.register(CustomUserPosts)
admin.site.register(Like)
admin.site.register(UserPosts,CustomUserPostsAdmin)


