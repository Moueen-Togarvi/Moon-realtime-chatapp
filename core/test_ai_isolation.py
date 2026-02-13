import os
import django
import asyncio
from channels.testing import WebsocketCommunicator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from app1.consumers import ChatConsumer
from app1.models import User, ChatRoom, Message

async def test_isolation():
    print("Setting up test data...")
    # Setup Data
    user1, _ = await User.objects.aget_or_create(username='test_user_isolation')
    user2, _ = await User.objects.aget_or_create(username='test_user_2')
    ai, _ = await User.objects.aget_or_create(username='AI_Assistant')
    
    # Room A: User1 + User2 (Normal Chat)
    room_a = await ChatRoom.objects.acreate(room_type='direct', created_by=user1)
    await room_a.participants.aadd(user1, user2)
    
    # Room B: User1 + AI (AI Chat) - just to ensure it exists
    room_b = await ChatRoom.objects.acreate(room_type='direct', created_by=user1)
    await room_b.participants.aadd(user1, ai)
    
    print(f"Room A (User+User): {room_a.id}")
    print(f"Room B (User+AI): {room_b.id}")
    
    # Clear AI messages
    await Message.objects.filter(sender=ai).adelete()
    
    # Connect to Room A
    print("Connecting to Room A...")
    communicator = WebsocketCommunicator(ChatConsumer.as_asgi(), f"/ws/chat/{room_a.id}/")
    communicator.scope['url_route'] = {'kwargs': {'room_id': str(room_a.id)}}
    communicator.scope['user'] = user1
    
    connected, _ = await communicator.connect()
    if not connected:
        print("Failed to connect!")
        return
    else:
        print("Connected.")
    
    # Send message in Room A
    print("Sending message in Room A...")
    await communicator.send_json_to({
        'type': 'chat_message',
        'content': 'Hello user2, make sure AI does not hear us.',
        'message_type': 'text'
    })
    
    # Wait for processing (trigger_ai_reply is async background task)
    print("Waiting for potential AI reply...")
    await asyncio.sleep(2)
    
    # Check if AI replied anywhere
    ai_msgs_count = await Message.objects.filter(sender=ai).acount()
    
    if ai_msgs_count == 0:
        print("PASS: No AI messages generated.")
    else:
        print(f"FAIL: AI generated {ai_msgs_count} messages!")
        async for msg in Message.objects.filter(sender=ai):
            print(f" - In Room {msg.room.id}: {msg.content}")

    await communicator.disconnect()
    
    # Clean up
    await room_a.adelete()
    await room_b.adelete()
    await user1.adelete()
    await user2.adelete()

if __name__ == "__main__":
    asyncio.run(test_isolation())
