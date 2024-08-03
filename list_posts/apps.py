from django.apps import AppConfig


class ListPostsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'list_posts'

    def ready(self):
        import list_posts.signals
        