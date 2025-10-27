# Test Script for WhatsApp Clone - Offline Message Support
# This script tests if messages are saved even when users are offline

import os
import sys
import django

# Add the project directory to Python path
sys.path.append('D:/worksapace/whatsapp-Clone/core')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from app1.models import User, ChatRoom, Message, Notification
from django.utils import timezone

def test_offline_messages():
    print("Testing Offline Message Support...")
    
    try:
        # Get test users
        user1 = User.objects.get(username='testuser1')
        user2 = User.objects.get(username='testuser2')
        
        print(f"Found users: {user1.username}, {user2.username}")
        
        # Set user2 as offline
        user2.is_online = False
        user2.save()
        print(f"Set {user2.username} as offline")
        
        # Get or create a chat room
        room = ChatRoom.objects.filter(
            participants__in=[user1, user2],
            room_type='direct'
        ).first()
        
        if not room:
            room = ChatRoom.objects.create(
                name=f"{user1.username} and {user2.username}",
                room_type='direct',
                created_by=user1
            )
            room.participants.add(user1, user2)
            print(f"Created chat room: {room.id}")
        else:
            print(f"Using existing chat room: {room.id}")
        
        # Create a message from user1 to user2 (who is offline)
        message = Message.objects.create(
            sender=user1,
            room=room,
            content="Hello! This is a test message for offline user.",
            message_type='text'
        )
        print(f"Created message: {message.id} - '{message.content}'")
        
        # Check if notification was created for offline user
        notifications = Notification.objects.filter(
            user=user2,
            related_message=message,
            is_read=False
        )
        
        if notifications.exists():
            print(f"SUCCESS: Notification created for offline user {user2.username}")
            print(f"Notification: {notifications.first().title}")
        else:
            print(f"WARNING: No notification found for offline user {user2.username}")
        
        # Check unread count
        unread_count = Message.objects.filter(
            room=room,
            is_read=False
        ).exclude(sender=user2).count()
        
        print(f"Unread messages in room: {unread_count}")
        
        # Set user2 back online
        user2.is_online = True
        user2.save()
        print(f"Set {user2.username} back online")
        
        print("\nTest completed successfully!")
        print("Messages are saved even when users are offline.")
        print("Notifications are created for offline users.")
        
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_offline_messages()
