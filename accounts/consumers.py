import base64
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.sender_id = self.scope['url_route']['kwargs']['sender_id']
        self.receiver_id = self.scope['url_route']['kwargs']['receiver_id']

        self.room_group_name = f'chat_{min(self.sender_id, self.receiver_id)}_{max(self.sender_id, self.receiver_id)}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        logger.info(f"WebSocket connected: {self.room_group_name}")

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json.get('message', '')
        sender_id = text_data_json.get('sender_id', '')
        receiver_id = text_data_json.get('receiver_id', '')
        sender_profile_pic = text_data_json.get('sender_profile_pic', '')

        # Encode the message before saving and broadcasting
        encoded_message = base64.b64encode(message.encode('utf-8')).decode('utf-8')
        print(f'--------------->{encoded_message}')
        logger.info(f"Received message from {sender_id}: {message}")

        # Save the message to the database
        await self.save_message(sender_id, receiver_id, message)

        # Broadcast the message to the room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': encoded_message,  # Send the encoded message
                'sender_id': sender_id,
                'receiver_id': receiver_id,
                'sender_profile_pic': sender_profile_pic
            }
        )

    async def chat_message(self, event):
        encoded_message = event['message']
        sender_id = event['sender_id']
        receiver_id = event['receiver_id']
        sender_profile_pic = event['sender_profile_pic']

        # Decode the message before sending it to the client
        message = base64.b64decode(encoded_message).decode('utf-8')

        await self.send(text_data=json.dumps({
            'message': message,
            'sender_id': sender_id,
            'receiver_id': receiver_id,
            'sender_profile_pic': sender_profile_pic
        }))

    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        try:
            Message.objects.create(sender_id=sender_id, receiver_id=receiver_id, content=content)
        except Exception as e:
            logger.error(f"Error saving message: {e}")
