from django.urls import path
from . import consumers
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

websocket_urlpatterns = [
    path('ws/chat/<slug:room_slug>/', consumers.ChatConsumer.as_asgi()),
]