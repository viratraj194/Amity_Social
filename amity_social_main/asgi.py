import os
from django.core.asgi import get_asgi_application

# 1. Set the settings module FIRST
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'amity_social_main.settings')

# 2. Initialize the ASGI application to load all middleware (including WhiteNoise)
django_asgi_app = get_asgi_application()

# 3. Import Channels routers AFTER get_asgi_application() to prevent registry crashes
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import accounts.routing 

# 4. Hand off HTTP traffic to the native Django ASGI app wrapper
application = ProtocolTypeRouter({
    "http": django_asgi_app,  # This natively includes WhiteNoise via your middleware stack!
    "websocket": AuthMiddlewareStack(
        URLRouter(
            accounts.routing.websocket_urlpatterns
        )
    ),
})