import json
import logging
import redis
import asyncio
from datetime import datetime, timezone
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, Room, User, MessageNotification

logger = logging.getLogger(__name__)


class ChatConsumer(AsyncWebsocketConsumer):
    # Class-level tracking for presence cleanup
    _active_connections = {}  # user_id -> set of room_slugs
    _cleanup_interval = 300  # 5 minutes in seconds
    _last_cleanup = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_conn = None
        self.user_rooms = set()  # Track rooms user is connected to
        self.user_id = None

    async def connect(self):
        self.room_slug = self.scope['url_route']['kwargs']['room_slug']
        self.room = await self.get_room()
        self.room_group_name = f'chat_{self.room_slug}'
        self.user_id = self.scope["user"].id

        # Initialize Redis connection BEFORE any sync calls
        self.redis_conn = redis.Redis()

        await self.accept()

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        # Join personal group for notifications
        await self.channel_layer.group_add(
            f"user_{self.user_id}",
            self.channel_name
        )

        # Track this room connection at class level
        self.user_rooms.add(self.room_slug)
        if self.user_id not in ChatConsumer._active_connections:
            ChatConsumer._active_connections[self.user_id] = set()
        ChatConsumer._active_connections[self.user_id].add(self.room_slug)

        # Set user as online in both Redis AND database (global presence)
        await self.set_user_status(self.user_id, 'online')

        # Add user to room-specific presence set
        await self.add_user_to_room_presence(self.room_slug, self.user_id)

        # Notify group about user status change
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user_id,
                'status': 'online'
            }
        )

        # Notify current user about the online status of other users in this room
        online_users = await self.get_online_users_in_room(self.room_slug)
        for uid in online_users:
            if uid != self.user_id:
                await self.send(text_data=json.dumps({
                    'type': 'user_status',
                    'user_id': uid,
                    'status': 'online'
                }))

        # Mark existing unread messages as read when entering the room
        read_message_ids = await self.mark_messages_as_read(self.user_id)
        if read_message_ids:
            await self.broadcast_status_updates(read_message_ids, Message.STATUS_READ)

        # Run periodic cleanup if needed
        await self.maybe_run_cleanup()

    async def disconnect(self, close_code):
        # Remove from room tracking
        self.user_rooms.discard(self.room_slug)

        # Update class-level tracking
        if self.user_id in ChatConsumer._active_connections:
            ChatConsumer._active_connections[self.user_id].discard(self.room_slug)
            if not ChatConsumer._active_connections[self.user_id]:
                del ChatConsumer._active_connections[self.user_id]

        # Remove user from room-specific presence set
        await self.remove_user_from_room_presence(self.room_slug, self.user_id)

        # Notify the group about user's disconnection
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user_id,
                'status': 'offline'
            }
        )

        # Remove user from room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Only set user offline globally if no more room connections
        if len(self.user_rooms) == 0:
            await self.set_user_status(self.user_id, 'offline')
        else:
            # User still connected to other rooms - notify those rooms
            for other_room_slug in self.user_rooms:
                await self.channel_layer.group_send(
                    f'chat_{other_room_slug}',
                    {
                        'type': 'user_status',
                        'user_id': self.user_id,
                        'status': 'online'  # Still online in other rooms
                    }
                )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        command = text_data_json.get('command', None)

        # Handle 'mark_as_read' command to mark messages as read
        if command == 'mark_as_read':
            message_ids = await self.mark_messages_as_read(self.scope["user"].id)
            # Broadcast status updates after marking as read
            if message_ids:
                await self.broadcast_status_updates(message_ids, Message.STATUS_READ)
            return

        # Handle sending a message
        message = text_data_json.get('message', '')
        sender_id = self.scope["user"].id
        receiver_id = text_data_json.get('receiver_id')
        sender_profile_pic = text_data_json.get('sender_profile_pic', '')

        if message:
            # Save message and get the message object
            message_obj = await self.save_message(sender_id, receiver_id, message)

            # Check if receiver is online in this room
            room_users = await self.get_online_users_in_room(self.room_slug)
            receiver_online = receiver_id in room_users

            message_status = Message.STATUS_SENT
            read_message_ids = []

            if receiver_online:
                # Receiver is online - mark message as delivered immediately
                if message_obj:
                    await self.update_message_status(message_obj.id, Message.STATUS_DELIVERED)
                    message_status = Message.STATUS_DELIVERED
                # Mark messages as read if receiver is in the same room
                read_message_ids = await self.mark_messages_as_read(receiver_id)
                # Broadcast read status for messages that were just read
                if read_message_ids:
                    await self.broadcast_status_updates(read_message_ids, Message.STATUS_READ)
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
            'type': 'user_status',
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

    async def maybe_run_cleanup(self):
        """Run periodic cleanup of stale Redis presence entries if enough time has passed"""
        import time
        now = time.time()
        if (ChatConsumer._last_cleanup is None or
                now - ChatConsumer._last_cleanup > ChatConsumer._cleanup_interval):
            await self.run_presence_cleanup()
            ChatConsumer._last_cleanup = now

    async def run_presence_cleanup(self):
        """Clean up stale entries in Redis presence sets"""
        try:
            if not self.redis_conn:
                self.redis_conn = redis.Redis()

            # Get all active room slugs from database
            active_rooms = await self.get_active_room_slugs()

            # Find stale room presence keys
            keys = self.redis_conn.keys('room_*_online')
            for key in keys:
                key_str = key.decode() if isinstance(key, bytes) else key
                # Extract room slug from key format: room_{slug}_online
                if key_str.startswith('room_') and key_str.endswith('_online'):
                    parts = key_str.split('_')
                    if len(parts) >= 3:
                        room_slug = '_'.join(parts[1:-1])
                        if room_slug not in active_rooms:
                            # Room no longer exists - clean up
                            self.redis_conn.delete(key)
                            logger.info(f'Cleaned up stale presence set: {key_str}')

            logger.info('Redis presence cleanup completed')
        except redis.RedisError as e:
            logger.error(f'Redis error during cleanup: {e}')
        except Exception as e:
            logger.error(f'Error during presence cleanup: {e}')

    @database_sync_to_async
    def get_active_room_slugs(self):
        """Get all active room slugs from database"""
        return set(Room.objects.values_list('slug', flat=True))

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
        """Set user status in both Redis and database (global presence)"""
        try:
            if not self.redis_conn:
                self.redis_conn = redis.Redis()

            if status == 'online':
                # Add to global online users set
                self.redis_conn.sadd('global_online_users', user_id)
                User.objects.filter(id=user_id).update(is_online=True)
            else:
                # Remove from global online users set
                self.redis_conn.srem('global_online_users', user_id)
                User.objects.filter(id=user_id).update(is_online=False)
        except redis.RedisError as e:
            logger.error(f"Error setting user status in Redis: {e}")
        except Exception as e:
            logger.error(f"Error updating user is_online in database: {e}")

    @database_sync_to_async
    def add_user_to_room_presence(self, room_slug, user_id):
        """Add user to room-specific presence set"""
        try:
            if not self.redis_conn:
                self.redis_conn = redis.Redis()
            self.redis_conn.sadd(f'room_{room_slug}_online', user_id)
        except redis.RedisError as e:
            logger.error(f"Error adding user to room presence: {e}")

    @database_sync_to_async
    def remove_user_from_room_presence(self, room_slug, user_id):
        """Remove user from room-specific presence set"""
        try:
            if not self.redis_conn:
                self.redis_conn = redis.Redis()
            self.redis_conn.srem(f'room_{room_slug}_online', user_id)
        except redis.RedisError as e:
            logger.error(f"Error removing user from room presence: {e}")

    @database_sync_to_async
    def get_online_users_in_room(self, room_slug):
        """Get online users for a specific room"""
        try:
            if not self.redis_conn:
                self.redis_conn = redis.Redis()
            online_users = self.redis_conn.smembers(f'room_{room_slug}_online')
            return [int(user_id.decode()) for user_id in online_users]
        except redis.RedisError as e:
            logger.error(f"Error retrieving online users from Redis: {e}")
            return []

    @database_sync_to_async
    def get_online_users(self):
        """Get all globally online users (legacy method - kept for compatibility)"""
        try:
            if not self.redis_conn:
                self.redis_conn = redis.Redis()
            online_users = self.redis_conn.smembers('global_online_users')
            return [int(user_id.decode()) for user_id in online_users]
        except redis.RedisError as e:
            logger.error(f"Error retrieving online users from Redis: {e}")
            return []

    @database_sync_to_async
    def mark_messages_as_read(self, user_id):
        """Mark messages and notifications as read for the current room"""
        try:
            now = datetime.now(timezone.utc)
            # Mark messages as read and collect their IDs for status broadcast
            messages = list(self.room.messages.filter(receiver_id=user_id, status__lt=Message.STATUS_READ))
            message_ids = [m.id for m in messages]
            # Reuse message_ids instead of re-running the query
            if message_ids:
                self.room.messages.filter(id__in=message_ids).update(status=Message.STATUS_READ, read_at=now)
            # Mark message notifications as read
            notifications = MessageNotification.objects.filter(
                user_id=user_id,
                room=self.room,
                is_read=False
            )
            notifications.update(is_read=True)
            return message_ids
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
            return []

    async def broadcast_status_updates(self, message_ids, status):
        """Broadcast message status updates to the channel group (batched)"""
        if not message_ids:
            return
        # Send all status updates in parallel for better performance
        await asyncio.gather(*[
            self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'message_status_update',
                    'message_id': msg_id,
                    'status': status
                }
            )
            for msg_id in message_ids
        ])

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
                    'last_message_time': last_message.created_at.isoformat() if last_message else None,
                    'unread_msg': unread_msg,
                })

            return rooms_with_photos
        except Exception as e:
            logger.error(f"Error retrieving rooms with photos: {e}")
            return []
