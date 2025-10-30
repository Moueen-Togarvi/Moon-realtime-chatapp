import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, TypingIndicator, UserPresence, Notification
from django.utils import timezone
import uuid

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope['user']

        print(f"WebSocket connection attempt: room_id={self.room_id}, user={self.user.username if self.user.is_authenticated else 'anonymous'}")

        if not self.user.is_authenticated:
            print("User not authenticated, closing connection")
            await self.close()
            return

        # Security check: Verify user is a participant in the room
        is_participant = await self.check_user_is_participant()
        if not is_participant:
            print(f"User {self.user.username} is not a participant in room {self.room_id}, closing connection")
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f"WebSocket connection accepted for room {self.room_id}")

        # Update user presence
        await self.update_user_presence(True)

        # Send online status to other users
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': str(self.user.id),
                'is_online': True,
                'username': self.user.username
            }
        )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # Update user presence
        await self.update_user_presence(False)

        # Send offline status to other users
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': str(self.user.id),
                'is_online': False,
                'username': self.user.username
            }
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            print(f"Received WebSocket message: {message_type} from user {self.user.username}")

            if message_type == 'chat_message':
                await self.handle_chat_message(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'stop_typing':
                await self.handle_stop_typing(data)
            elif message_type == 'message_read':
                await self.handle_message_read(data)
        except Exception as e:
            print(f"Error processing WebSocket message: {e}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Error processing message'
            }))

    async def handle_chat_message(self, data):
        content = data.get('content', '').strip()
        message_type = data.get('message_type', 'text')
        media_file = data.get('media_file')
        reply_to_id = data.get('reply_to')

        print(f"Handling chat message: content='{content}', type='{message_type}', media='{media_file}'")

        if not content and not media_file:
            print("No content or media file provided")
            return

        # Save message to database (always save, even if user is offline)
        message = await self.save_message(content, message_type, media_file, reply_to_id)
        
        if not message:
            print("Failed to save message")
            return

        print(f"Message saved with ID: {message.id}")

        # Create message data for broadcasting
        message_data = {
            'id': str(message.id),
            'sender': {
                'id': str(message.sender.id),
                'username': message.sender.username,
                'profile_picture': message.sender.profile_picture.url if message.sender.profile_picture else None
            },
            'content': message.content,
            'message_type': message.message_type,
            'media_file': message.media_file.url if message.media_file else None,
            'timestamp': message.timestamp.isoformat(),
            'is_read': message.is_read,
            'reply_to': str(message.reply_to.id) if message.reply_to else None
        }

        # Send message to room group (for online users)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message_data
            }
        )
        print("Message broadcasted to room group")

        # Create notifications for offline users
        await self.create_notifications_for_offline_users(message)

    async def handle_typing(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'is_typing': True
            }
        )

    async def handle_stop_typing(self, data):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user_id': str(self.user.id),
                'username': self.user.username,
                'is_typing': False
            }
        )

    async def handle_message_read(self, data):
        message_id = data.get('message_id')
        await self.mark_message_as_read(message_id)

    # WebSocket event handlers
    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_typing': event['is_typing']
        }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'username': event['username'],
            'is_online': event['is_online']
        }))

    # Database operations
    @database_sync_to_async
    def save_message(self, content, message_type, media_file, reply_to_id):
        try:
            print(f"Saving message: room_id={self.room_id}, sender={self.user.username}, content='{content}'")
            room = ChatRoom.objects.get(id=self.room_id)
            reply_to = None
            if reply_to_id:
                try:
                    reply_to = Message.objects.get(id=reply_to_id)
                except Message.DoesNotExist:
                    pass

            message = Message.objects.create(
                sender=self.user,
                room=room,
                content=content,
                message_type=message_type,
                reply_to=reply_to
            )
            print(f"Message created successfully: {message.id}")
            return message
        except ChatRoom.DoesNotExist:
            print(f"ChatRoom with id {self.room_id} does not exist")
            return None
        except Exception as e:
            print(f"Error saving message: {e}")
            return None

    @database_sync_to_async
    def mark_message_as_read(self, message_id):
        try:
            message = Message.objects.get(id=message_id)
            if self.user not in message.read_by.all():
                message.read_by.add(self.user)
                message.is_read = True
                message.save()
        except Message.DoesNotExist:
            pass

    @database_sync_to_async
    def create_notifications_for_offline_users(self, message):
        """Create notifications for offline users in the chat room"""
        try:
            # Get all participants in the room except the sender
            participants = message.room.participants.exclude(id=message.sender.id)
            
            for participant in participants:
                # Check if user is offline
                if not participant.is_online:
                    # Create notification
                    Notification.objects.create(
                        user=participant,
                        notification_type='message',
                        title=f'New message from {message.sender.username}',
                        message=message.content[:100] + '...' if len(message.content) > 100 else message.content,
                        related_message=message,
                        related_room=message.room
                    )
                    print(f"Created notification for offline user: {participant.username}")
        except Exception as e:
            print(f"Error creating notifications: {e}")

    @database_sync_to_async
    def check_user_is_participant(self):
        """Check if user is a participant in the room"""
        try:
            room = ChatRoom.objects.get(id=self.room_id, is_active=True)
            return self.user in room.participants.all()
        except ChatRoom.DoesNotExist:
            return False

    @database_sync_to_async
    def update_user_presence(self, is_online):
        presence, created = UserPresence.objects.get_or_create(user=self.user)
        presence.is_online = is_online
        presence.last_seen = timezone.now()
        presence.save()

        # Update user model
        self.user.is_online = is_online
        self.user.last_seen = timezone.now()
        self.user.save()


class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return

        self.user_group_name = f'notifications_{self.user.id}'
        
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        # Handle any client-side notifications if needed
        pass

    async def notification_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification']
        }))
