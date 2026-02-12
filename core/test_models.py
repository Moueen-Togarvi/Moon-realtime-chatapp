import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
import django
django.setup()
from django.conf import settings
import google.generativeai as genai

# Configure the API key
api_key = getattr(settings, 'GEMINI_API_KEY')
if api_key:
    genai.configure(api_key=api_key)
    print("API key configured successfully")
else:
    print("No API key found")
    exit(1)

print("\nTrying to use gemini-2.0-flash model:")
try:
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content('Hello, world!')
    print(f"Response: {response.text[:100]}")
except Exception as e:
    print(f"Error with gemini-2.0-flash: {e}")

print("\nTrying to use gemini-flash-latest model:")
try:
    model = genai.GenerativeModel('gemini-flash-latest')
    response = model.generate_content('Hello, world!')
    print(f"Response: {response.text[:100]}")
except Exception as e:
    print(f"Error with gemini-flash-latest: {e}")