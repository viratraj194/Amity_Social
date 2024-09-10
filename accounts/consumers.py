import json
import logging
import redis
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, Room, User

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_conn = None

    async def connect(self):
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.room = await self.get_room()
        self.room_group_name = f'chat_{self.room_slug}'

        await self.accept()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.set_user_status(self.scope["user"].id, 'online')

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.scope["user"].id,
                'status': 'online'
            }
        )

        online_users = await self.get_online_users()
        for user_id in online_users:
            if user_id != self.scope["user"].id:
                await self.send(text_data=json.dumps({
                    'user_id': user_id,
                    'status': 'online'
                }))

        logger.info(f"WebSocket connected: {self.room_group_name}")

        rooms_with_photos = await self.get_rooms_with_photos(self.scope["user"].id)
        await self.send(text_data=json.dumps({
            'rooms_with_photos': rooms_with_photos
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.scope["user"].id,
                'status': 'offline'
            }
        )

        await self.set_user_status(self.scope["user"].id, 'offline')

        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        logger.info(f"WebSocket disconnected: {self.room_group_name}")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        sender_id = self.scope["user"].id
        receiver_id = text_data_json.get('receiver_id')
        sender_profile_pic = text_data_json.get('sender_profile_pic', '')

        if message:
            await self.save_message(sender_id, receiver_id, message)

            room_users = await self.get_online_users()
            if sender_id in room_users and receiver_id in room_users:
                await self.mark_messages_as_read(receiver_id)

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
            Message.objects.create(sender_id=sender_id, receiver_id=receiver_id, room=self.room, content=content)
        except Exception as e:
            logger.error(f"Error saving message: {e}")

    @database_sync_to_async
    def set_user_status(self, user_id, status):
        try:
            if not self.redis_conn:
                self.redis_conn = redis.Redis()
                
            if status == 'online':
                self.redis_conn.sadd(f'room_{self.room_slug}_online', user_id)
            else:
                self.redis_conn.srem(f'room_{self.room_slug}_online', user_id)
        except redis.RedisError as e:
            logger.error(f"Error setting user status in Redis: {e}")

    @database_sync_to_async
    def get_online_users(self):
        try:
            if not self.redis_conn:
                self.redis_conn = redis.Redis()

            online_users = self.redis_conn.smembers(f'room_{self.room_slug}_online')
            return [int(user_id.decode()) for user_id in online_users]
        except redis.RedisError as e:
            logger.error(f"Error retrieving online users from Redis: {e}")
            return []

    @database_sync_to_async
    def mark_messages_as_read(self, user_id):
        try:
            messages = self.room.messages.filter(receiver_id=user_id, read=False)
            messages.update(read=True)
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")

    @database_sync_to_async
    def get_room(self):
        try:
            return Room.objects.get(slug=self.room_slug)
        except Room.DoesNotExist:
            logger.error(f"Room with slug {self.room_slug} does not exist.")
            return None

    @database_sync_to_async
    def get_rooms_with_photos(self, sender_id):
        try:
            sender = User.objects.get(id=sender_id)
            rooms = Room.objects.filter(participants=sender)
            rooms_with_photos = []

            for room in rooms:
                other_participants = room.participants.exclude(id=sender.id)
                other_user = other_participants.first()
                last_message = room.get_last_message()
                unread_msg = room.has_unread_messages(sender)
                rooms_with_photos.append({
                    'room_id': room.id,
                    'room_name': room.name,
                    'room_slug': room.slug,
                    'other_user_id': other_user.id,
                    'other_user_name': other_user.username,
                    'profile_photo_url': other_user.userprofile.profile_picture.url,
                    'last_message_content': last_message.content if last_message else '',
                    'unread_msg': unread_msg,
                })

            return rooms_with_photos
        except Exception as e:
            logger.error(f"Error retrieving rooms with photos: {e}")
            return []
