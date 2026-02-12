import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Test WebSocket broadcasting
from app1.views import ai_reply
from app1.models import User, ChatRoom, Message
from django.http import HttpRequest
from django.test import RequestFactory
import json

# Create a mock request
factory = RequestFactory()

# Create test users if they don't exist
user1, created = User.objects.get_or_create(
    username='testuser1',
    defaults={
        'email': 'testuser1@example.com',
        'first_name': 'Test',
        'last_name': 'User1'
    }
)

user2, created = User.objects.get_or_create(
    username='testuser2',
    defaults={
        'email': 'testuser2@example.com',
        'first_name': 'Test',
        'last_name': 'User2'
    }
)

# Get or create AI assistant
ai_user, created = User.objects.get_or_create(
    username='AI_Assistant',
    defaults={
        'email': 'ai@example.com',
        'first_name': 'AI',
        'last_name': 'Assistant',
        'is_active': True
    }
)

# Create a test chat room with multiple participants
room = ChatRoom.objects.create(
    room_type='direct',
    created_by=ai_user
)
room.participants.add(user1, user2, ai_user)

print(f"Created test room with ID: {room.id}")

# Test AI request with room ID
print("\nTesting AI request with room ID...")
form_request = factory.post('/ai/reply/', data={
    'text': 'Hello, what is your name?',
    'room_id': str(room.id)
})

# Simulate an authenticated user
form_request.user = user1

form_response = ai_reply(form_request)
print(f"AI Response Status: {form_response.status_code}")
response_data = json.loads(form_response.content.decode())
print(f"AI Response Content: {response_data}")

# Check messages in the room
messages = Message.objects.filter(room=room).order_by('timestamp')
print(f"\nMessages in room ({messages.count()} total):")
for msg in messages:
    print(f"  - {msg.sender.username}: {msg.content}")

# Check if AI user is a participant
print(f"\nRoom participants:")
for participant in room.participants.all():
    print(f"  - {participant.username}")