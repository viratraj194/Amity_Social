import json
import logging
import redis
from datetime import timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, Room, User, MessageNotification

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

        # Join personal group for notifications
        await self.channel_layer.group_add(
            f"user_{self.scope['user'].id}",
            self.channel_name
        )

        await self.set_user_status(self.scope["user"].id, 'online')

        # Notify group about user status change
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.scope["user"].id,
                'status': 'online'
            }
        )

        # Notify current user about the online status of other users
        
        online_users = await self.get_online_users()
        for user_id in online_users:
            if user_id != self.scope["user"].id:
                await self.send(text_data=json.dumps({
                    'user_id': user_id,
                    'status': 'online'
                }))

        # Send rooms with profile photos
        rooms_with_photos = await self.get_rooms_with_photos(self.scope["user"].id)
        await self.send(text_data=json.dumps({
            'rooms_with_photos': rooms_with_photos
        }))

    async def disconnect(self, close_code):
        # Notify the group about user's disconnection
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.scope["user"].id,
                'status': 'offline'
            }
        )

        # Set user status as offline in Redis
        await self.set_user_status(self.scope["user"].id, 'offline')

        # Remove user from room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        command = text_data_json.get('command', None)

        # Handle 'mark_as_read' command to mark messages as read
        if command == 'mark_as_read':
            await self.mark_messages_as_read(self.scope["user"].id)
            return

        # Handle sending a message
        message = text_data_json.get('message', '')
        sender_id = self.scope["user"].id
        receiver_id = text_data_json.get('receiver_id')
        sender_profile_pic = text_data_json.get('sender_profile_pic', '')

        if message:
            # Save message and get the message object
            message_obj = await self.save_message(sender_id, receiver_id, message)

            # Check if receiver is online
            room_users = await self.get_online_users()
            receiver_online = receiver_id in room_users

            message_status = Message.STATUS_SENT
            if receiver_online:
                # Receiver is online - mark message as delivered immediately
                if message_obj:
                    await self.update_message_status(message_obj.id, Message.STATUS_DELIVERED)
                    message_status = Message.STATUS_DELIVERED
                # Mark messages as read if receiver is in the same room
                await self.mark_messages_as_read(receiver_id)
            else:
                # Receiver offline - create persistent notification
                await self.create_message_notification(message_obj.id if message_obj else None)

            # Send message to room group with status and message ID
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': sender_id,
                    'sender_profile_pic': sender_profile_pic,
                    'room_slug': self.room_slug,
                    'message_id': message_obj.id if message_obj else None,
                    'status': message_status,
                    'update_room_list': True  # Flag to update room list ordering
                }
            )
            # 🔔 Send WebSocket notification to receiver (if connected via another tab)
            await self.channel_layer.group_send(
                f"user_{receiver_id}",
                {
                    "type": "new_notification",
                    "room_slug": self.room_slug,
                    "unread": True
                }
            )

            # Broadcast room list update to all participants
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'room_list_update',
                    'room_slug': self.room_slug,
                    'last_message': message,
                    'last_message_time': now.isoformat()
                }
            )
    async def chat_message(self, event):
        # Handle the message event to send to WebSocket
        message = event['message']
        sender_id = event['sender_id']
        sender_profile_pic = event['sender_profile_pic']
        room_slug = event['room_slug']
        message_id = event.get('message_id', None)
        status = event.get('status', Message.STATUS_SENT)

        await self.send(text_data=json.dumps({
            "type": "chat_message",
            "message": message,
            "sender_id": sender_id,
            "sender_profile_pic": sender_profile_pic,
            "room_slug": room_slug,
            "message_id": message_id,
            "status": status
        }))

    async def user_status(self, event):
        # Handle user status change
        user_id = event['user_id']
        status = event['status']

        await self.send(text_data=json.dumps({
            'user_id': user_id,
            'status': status
        }))

    async def new_notification(self, event):
        await self.send(text_data=json.dumps({
            "type": "new_notification",
            "room_slug": event["room_slug"],
            "unread": event["unread"]
        }))

    async def message_status_update(self, event):
        """Handle message status update event"""
        message_id = event['message_id']
        status = event['status']

        await self.send(text_data=json.dumps({
            "type": "message_status_update",
            "message_id": message_id,
            "status": status
        }))

    async def room_list_update(self, event):
        """Handle room list update event"""
        room_slug = event['room_slug']
        last_message = event['last_message']
        last_message_time = event['last_message_time']

        await self.send(text_data=json.dumps({
            "type": "room_list_update",
            "room_slug": room_slug,
            "last_message": last_message,
            "last_message_time": last_message_time
        }))



    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        try:
            return Message.objects.create(sender_id=sender_id, receiver_id=receiver_id, room=self.room, content=content)
        except Exception as e:
            logger.error(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def create_message_notification(self, message_id):
        """Create persistent notification when receiver is offline"""
        try:
            if not message_id:
                return
            message = Message.objects.select_related('sender', 'receiver', 'room').get(id=message_id)
            if not message.receiver.is_online:
                MessageNotification.objects.create(
                    user=message.receiver,
                    sender=message.sender,
                    room=message.room,
                    message=message
                )
        except Exception as e:
            logger.error(f"Error creating message notification: {e}")

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
        """Mark messages and notifications as read for the current room"""
        try:
            from datetime import datetime
            now = datetime.now(timezone.utc)
            # Mark messages as read and collect their IDs for status broadcast
            messages = list(self.room.messages.filter(receiver_id=user_id, status__lt=Message.STATUS_READ))
            message_ids = [m.id for m in messages]
            messages_update = self.room.messages.filter(receiver_id=user_id, status__lt=Message.STATUS_READ)
            messages_update.update(status=Message.STATUS_READ, read_at=now)
            # Mark message notifications as read
            notifications = MessageNotification.objects.filter(
                user_id=user_id,
                room=self.room,
                is_read=False
            )
            notifications.update(is_read=True)
            # Broadcast status updates to sender
            for msg_id in message_ids:
                self.send_status_update(msg_id, Message.STATUS_READ)
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")

    def send_status_update(self, message_id, status):
        """Send message status update to the channel group"""
        try:
            # This needs to be called from async context, so we use async_to_sync if needed
            import asyncio
            from asgiref.sync import async_to_sync
            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'message_status_update',
                    'message_id': message_id,
                    'status': status
                }
            )
        except Exception as e:
            logger.error(f"Error sending status update: {e}")

    @database_sync_to_async
    def update_message_status(self, message_id, status):
        """Update message status (sent/delivered/read)"""
        try:
            from datetime import datetime
            now = datetime.now(timezone.utc)
            message = Message.objects.get(id=message_id)
            update_kwargs = {'status': status}
            if status == Message.STATUS_DELIVERED:
                update_kwargs['delivered_at'] = now
            elif status == Message.STATUS_READ:
                update_kwargs['read_at'] = now
            Message.objects.filter(id=message_id).update(**update_kwargs)
        except Exception as e:
            logger.error(f"Error updating message status: {e}")

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
            sender = User.objects.select_related('userprofile').get(id=sender_id)
            # Optimize: prefetch participants, last message, and use annotated unread count
            rooms = Room.objects.filter(participants=sender).prefetch_related(
                'participants__userprofile'
            )
            rooms_with_photos = []

            for room in rooms:
                other_participants = [p for p in room.participants.all() if p.id != sender.id]
                other_user = other_participants[0] if other_participants else None
                if not other_user:
                    continue

                # Get last message efficiently
                last_message = room.messages.order_by('-created_at').first()
                # Check for unread messages using status field
                unread_msg = room.messages.filter(receiver=sender, status__lt=Message.STATUS_READ).exists()

                profile_photo_url = getattr(other_user, 'userprofile', None)
                if profile_photo_url and hasattr(profile_photo_url, 'profile_picture'):
                    profile_photo_url = profile_photo_url.profile_picture.url
                else:
                    profile_photo_url = 'static/img/images.jpeg'

                rooms_with_photos.append({
                    'room_id': room.id,
                    'room_name': room.name,
                    'room_slug': room.slug,
                    'other_user_id': other_user.id,
                    'other_user_name': other_user.username,
                    'profile_photo_url': profile_photo_url,
                    'last_message_content': last_message.content if last_message else '',
                    'unread_msg': unread_msg,
                })

            return rooms_with_photos
        except Exception as e:
            logger.error(f"Error retrieving rooms with photos: {e}")
            return []
