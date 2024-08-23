import json
import logging
import redis
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, Room, User
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)
class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get the room_slug from the URL route
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']

        # Fetch the Room object based on the slug
        self.room = await database_sync_to_async(Room.objects.get)(slug=self.room_slug)

        # Create a unique room group name
        self.room_group_name = f'chat_{self.room_slug}'

        # Accept the WebSocket connection
        await self.accept()

        # Add the user to the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Set the user status to online in Redis
        await self.set_user_status(self.scope["user"].id, 'online')

        # Notify other users in the room of this user's online status
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.scope["user"].id,
                'status': 'online'
            }
        )

        # Send back the status of all other users currently online in the room
        online_users = await self.get_online_users()
        for user_id in online_users:
            if user_id != self.scope["user"].id:
                await self.send(text_data=json.dumps({
                    'user_id': user_id,
                    'status': 'online'
                }))

        logger.info(f"WebSocket connected: {self.room_group_name}")

    async def disconnect(self, close_code):
        # Notify other users of this user's offline status
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.scope["user"].id,
                'status': 'offline'
            }
        )

        # Set user status to offline in Redis
        await self.set_user_status(self.scope["user"].id, 'offline')

        # Remove the user from the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected: {self.room_group_name}")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        sender_id = self.scope["user"].id  # The current user is the sender
        receiver_id = text_data_json.get('receiver_id')
        sender_profile_pic = text_data_json.get('sender_profile_pic', '')

        # Save the message to the database
        await self.save_message(sender_id, receiver_id, message)

        # Broadcast the message to the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': sender_id,
                'sender_profile_pic': sender_profile_pic
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender_id = event['sender_id']
        sender_profile_pic = event['sender_profile_pic']

        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
            'sender_profile_pic': sender_profile_pic
        }))

    async def user_status(self, event):
        user_id = event['user_id']
        status = event['status']

        await self.send(text_data=json.dumps({
            'user_id': user_id,
            'status': status
        }))

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        try:
            # Create and save the message associated with the room
            Message.objects.create(sender_id=sender_id, receiver_id=receiver_id, room=self.room, content=content)
        except Exception as e:
            logger.error(f"Error saving message: {e}")

    @database_sync_to_async
    def set_user_status(self, user_id, status):
        try:
            r = redis.Redis()  # Configure Redis if needed
            if status == 'online':
                r.sadd(f'room_{self.room_slug}_online', user_id)
            else:
                r.srem(f'room_{self.room_slug}_online', user_id)
        except redis.RedisError as e:
            logger.error(f"Error setting user status in Redis: {e}")

    @database_sync_to_async
    def get_online_users(self):
        try:
            r = redis.Redis()
            online_users = r.smembers(f'room_{self.room_slug}_online')
            return [int(user_id.decode()) for user_id in online_users]
        except redis.RedisError as e:
            logger.error(f"Error retrieving online users from Redis: {e}")
            return []
