
import os
import django
import asyncio
from channels.db import database_sync_to_async

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from app1.models import User, Message, ChatRoom
from app1.consumers import ChatConsumer

async def test_serialization():
    # create dummy user and message
    username = 'test_serializer_user'
    try:
        user = await database_sync_to_async(User.objects.create_user)(username=username, password='password')
        print(f"Created user: {user.username}, profile_picture: {user.profile_picture}")
        
        # Check profile picture logic directly
        pic_url = user.profile_picture.url if user.profile_picture else None
        print(f"Profile picture URL check 1 (direct): {pic_url}")
        
        pic_url_getattr = user.profile_picture.url if getattr(user, 'profile_picture', None) else None
        print(f"Profile picture URL check 2 (getattr): {pic_url_getattr}")
        
        # Create room and message
        room = await database_sync_to_async(ChatRoom.objects.create)(created_by=user)
        message = await database_sync_to_async(Message.objects.create)(sender=user, room=room, content="test")
        
        consumer = ChatConsumer()
        # Mocking serialized methods since we can't instantiate consumer fully without scope
        serialized = await consumer.serialize_message(message)
        print("Serialization successful:", serialized)
        
    except Exception as e:
        print("Serialization FAILED:", e)
    finally:
        # Cleanup
        if 'user' in locals():
            await database_sync_to_async(user.delete)()

if __name__ == '__main__':
    asyncio.run(test_serialization())
