import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Test the AI reply endpoint
from app1.views import ai_reply
from django.http import HttpRequest
from django.test import RequestFactory
import json

# Create a mock request
factory = RequestFactory()

print("Testing AI reply endpoint...")

# Test form data request
print("\n1. Testing form data request...")
form_request = factory.post('/ai/reply/', data={
    'text': 'What is the capital of France?'
})

form_response = ai_reply(form_request)
print(f"Status: {form_response.status_code}")
response_data = json.loads(form_response.content.decode())
print(f"Response: {response_data}")

# Test JSON request
print("\n2. Testing JSON request...")
import json as json_module
json_request = factory.post('/ai/reply/', 
    data=json_module.dumps({'prompt': 'What is the capital of Germany?'}),
    content_type='application/json')

json_response = ai_reply(json_request)
print(f"Status: {json_response.status_code}")
json_response_data = json.loads(json_response.content.decode())
print(f"Response: {json_response_data}")

print("\nTest completed!")