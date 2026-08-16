from django.contrib import admin
from django.db.models import Count
from .models import UserPosts,Like,Notification,Comment,UserSavedPosts,PostReport


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

class FlaggedPost(UserPosts):
    class Meta:
        proxy = True
        verbose_name = 'Flagged Post'
        verbose_name_plural = 'Flagged Posts'

class FlaggedPostAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'report_count')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(report_count=Count('reports')).filter(report_count__gte=50)

    def report_count(self, obj):
        return getattr(obj, 'report_count', 0)
    report_count.short_description = 'Report Count'
    report_count.admin_order_field = 'report_count'


admin.site.register(UserSavedPosts)
admin.site.register(Comment)

admin.site.register(Notification,NotificationAdmin)
admin.site.register(Like)
admin.site.register(UserPosts,CustomUserPostsAdmin)
admin.site.register(PostReport)
admin.site.register(FlaggedPost, FlaggedPostAdmin)


