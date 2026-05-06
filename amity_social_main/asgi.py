import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from whitenoise.asgi import AsgiWhiteNoise  # <--- Clean ASGI Wrapper for WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amity_social_main.settings')

# Initialize Django ASGI application early to ensure the app registry is loaded
django_asgi_app = get_asgi_application()

# Import your routing after initializing the core application
import accounts.routing 

application = ProtocolTypeRouter({
    "http": AsgiWhiteNoise(django_asgi_app),  # <--- Wrap the HTTP router here!
    "websocket": AuthMiddlewareStack(
        URLRouter(
            accounts.routing.websocket_urlpatterns
        )
    ),
})