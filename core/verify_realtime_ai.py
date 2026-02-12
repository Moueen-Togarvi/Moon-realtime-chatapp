import asyncio
import websockets
import json
import os
import django
from django.conf import settings
from asgiref.sync import sync_to_async

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from app1.models import User, ChatRoom, Message

@sync_to_async
def get_or_create_entities():
    user = User.objects.get(username='moon32') # Use an existing user
    ai_user, _ = User.objects.get_or_create(username='AI_Assistant')
    
    # Get or create an AI room
    room = ChatRoom.objects.filter(participants__username='AI_Assistant').filter(participants=user).first()
    if not room:
        room = ChatRoom.objects.create(room_type='direct', created_by=user)
        room.participants.add(user, ai_user)
    
    return str(user.id), str(room.id)

async def test_ai_realtime():
    # 1. Setup/Get Data
    user_id, room_id = await get_or_create_entities()
    print(f"Testing for User ID: {user_id} in Room: {room_id}")

    # 2. Connect to WebSocket
    uri = f"ws://127.0.0.1:8000/ws/chat/{room_id}/"
    
    # Note: We are connecting without a cookies/session, which might fail 
    # if ChatConsumer is strict. However, Daphne/Channels might allow it in dev
    # or if we are lucky. If it fails, we'll know.
    
    try:
        # In this env, we might not have a browser session, so ChatConsumer 
        # 'self.scope["user"].is_authenticated' will be false.
        # To truly test, we'd need a session cookie.
        # But let's try and see the error.
        
        async with websockets.connect(uri) as websocket:
            print("Connected to WebSocket.")
            
            # Send a chat message
            test_message = {
                'type': 'chat_message',
                'content': 'Hello AI, please reply in one word.',
                'message_type': 'text'
            }
            await websocket.send(json.dumps(test_message))
            print("Message sent.")

            # Wait for responses
            responses_received = []
            try:
                for _ in range(10):
                    resp = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(resp)
                    print(f"Received: {data['type']}")
                    responses_received.append(data)
                    if data['type'] == 'chat_message' and data['message']['sender']['username'] == 'AI_Assistant':
                        print(f"AI replied: {data['message']['content']}")
                        break
            except asyncio.TimeoutError:
                print("Timed out waiting for AI reply.")

            if any(r['type'] == 'chat_message' and r['message']['sender']['username'] == 'AI_Assistant' for r in responses_received):
                print("SUCCESS: Real-time AI reply received via WebSocket!")
            else:
                print("FAILURE: No real-time AI reply received.")

    except Exception as e:
        print(f"Connection failed: {e}")
        print("Note: This might be due to missing authentication in the test script.")

if __name__ == "__main__":
    asyncio.run(test_ai_realtime())
