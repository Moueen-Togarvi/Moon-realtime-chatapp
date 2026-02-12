# WebSocket Test Script for WhatsApp Clone
# Run this to test if WebSocket is working properly

import asyncio
import websockets
import json
import uuid

async def test_websocket():
    # Test WebSocket connection
    room_id = "5070aad8-1f27-43f3-8827-2e66220782be"  # Test room ID
    uri = f"ws://127.0.0.1:8000/ws/chat/{room_id}/"
    
    print(f"Connecting to: {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("SUCCESS: WebSocket connected successfully!")
            
            # Send a test message
            test_message = {
                "type": "chat_message",
                "content": "Hello from WebSocket test!",
                "message_type": "text"
            }
            
            await websocket.send(json.dumps(test_message))
            print("SUCCESS: Test message sent!")
            
            # Wait for response
            response = await websocket.recv()
            print(f"SUCCESS: Response received: {response}")
            
    except Exception as e:
        print(f"ERROR: WebSocket connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure Daphne server is running: daphne -b 127.0.0.1 -p 8000 core.asgi:application")
        print("2. Check if port 8000 is available")
        print("3. Verify ASGI configuration in core/asgi.py")

if __name__ == "__main__":
    print("Testing WebSocket Connection...")
    asyncio.run(test_websocket())