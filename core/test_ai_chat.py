import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Test the AI reply function directly
from app1.views import ai_reply
from django.http import HttpRequest
from django.test import RequestFactory

# Create a mock request
factory = RequestFactory()

# Test JSON request
print("Testing JSON request...")
json_request = factory.post('/ai/reply/', data='{"prompt": "What is Django?"}', content_type='application/json')
json_response = ai_reply(json_request)
print(f"JSON Response Status: {json_response.status_code}")
print(f"JSON Response Content: {json_response.content.decode()}")

print("\n" + "="*50 + "\n")

# Test form data request
print("Testing form data request...")
form_request = factory.post('/ai/reply/', data={'text': 'What is Python?'})
form_response = ai_reply(form_request)
print(f"Form Response Status: {form_response.status_code}")
print(f"Form Response Content: {form_response.content.decode()}")