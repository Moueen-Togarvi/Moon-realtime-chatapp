import requests
import json

# Test the AI reply endpoint
url = 'http://127.0.0.1:8080/ai/reply/'

# Test with JSON data
data = {
    'prompt': 'What is the capital of France?'
}

headers = {
    'Content-Type': 'application/json'
}

try:
    response = requests.post(url, data=json.dumps(data), headers=headers)
    print("JSON Request Test:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error with JSON request: {e}")

print("\n" + "="*50 + "\n")

# Test with form data
form_data = {
    'text': 'What is the capital of Germany?'
}

try:
    response = requests.post(url, data=form_data)
    print("Form Data Request Test:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error with form data request: {e}")

print("\n" + "="*50 + "\n")

# Test with chat room integration
form_data_with_room = {
    'text': 'What is the capital of Italy?',
    'room_id': 'test-room-id'
}

try:
    response = requests.post(url, data=form_data_with_room)
    print("Form Data with Room ID Request Test:")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error with form data and room ID request: {e}")