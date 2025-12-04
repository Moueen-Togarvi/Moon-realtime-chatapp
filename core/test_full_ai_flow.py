import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Test the full AI chat flow
from app1.views import ai_reply
from app1.models import User, ChatRoom, Message
from django.http import HttpRequest
from django.test import RequestFactory
import json

# Create a mock request
factory = RequestFactory()

# Create test user if it doesn't exist
user1, created = User.objects.get_or_create(
    username='testuser1',
    defaults={
        'email': 'testuser1@example.com',
        'first_name': 'Test',
        'last_name': 'User1'
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

# Create a test chat room
room = ChatRoom.objects.create(
    room_type='direct',
    created_by=ai_user
)
room.participants.add(user1, ai_user)

print(f"Created test room with ID: {room.id}")

# Test AI request with room ID (simulating chat room usage)
print("\nTesting AI request with room ID (chat room scenario)...")
form_request = factory.post('/ai/reply/', data={
    'text': 'Hello AI, what can you help me with?',
    'room_id': str(room.id)
})

# Simulate an authenticated user
form_request.user = user1
# Create a simple mock user object with is_authenticated property
class MockUser:
    def __init__(self, user):
        self.user = user
        self.is_authenticated = True
    def __getattr__(self, name):
        return getattr(self.user, name)

form_request.user = MockUser(user1)

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

print("\nTest completed!")