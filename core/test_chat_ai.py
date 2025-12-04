import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Test the AI reply function with room integration
from app1.views import ai_reply
from django.http import HttpRequest
from django.test import RequestFactory
from app1.models import User, ChatRoom
import uuid

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

# Create a test chat room
room = ChatRoom.objects.create(
    room_type='direct',
    created_by=user1
)
room.participants.add(user1, user2)

print(f"Created test room with ID: {room.id}")

# Test AI request with room ID
print("Testing AI request with room ID...")
form_request = factory.post('/ai/reply/', data={
    'text': 'What is the capital of France?',
    'room_id': str(room.id)
})

# Simulate an authenticated user
form_request.user = user1

form_response = ai_reply(form_request)
print(f"AI Response Status: {form_response.status_code}")
print(f"AI Response Content: {form_response.content.decode()}")

# Check if AI user was created and added to the room
try:
    ai_user = User.objects.get(username='AI_Assistant')
    print(f"AI User created: {ai_user.username}")
    
    # Check if AI user is a participant in the room
    if room.participants.filter(id=ai_user.id).exists():
        print("AI User is a participant in the room")
    else:
        print("AI User is NOT a participant in the room")
        
except User.DoesNotExist:
    print("AI User not found")