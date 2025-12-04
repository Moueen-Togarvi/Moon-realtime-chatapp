import os
import django
from django.conf import settings

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Test direct Gemini API call
def test_gemini_api():
    """Test direct Gemini API call"""
    try:
        # Import the required modules
        import google.generativeai as genai
        from django.conf import settings
        
        # Get API key from settings
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        
        if not api_key:
            print("ERROR: GEMINI_API_KEY not found in settings")
            return False
            
        # Configure the API
        genai.configure(api_key=api_key)
        
        # Test with the working model name
        model_name = getattr(settings, 'GEMINI_MODEL', None) or 'gemini-flash-latest'
        print(f"Using model: {model_name}")
        
        # Create the model
        model = genai.GenerativeModel(model_name)
        
        # Test prompt
        prompt = "What is the capital of France?"
        print(f"Sending prompt: {prompt}")
        
        # Generate content
        response = model.generate_content(prompt)
        
        # Extract the text response
        if hasattr(response, 'text'):
            print(f"Response: {response.text}")
            return True
        else:
            print("ERROR: No text in response")
            return False
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Gemini API connection...")
    success = test_gemini_api()
    if success:
        print("SUCCESS: Gemini API is working correctly!")
    else:
        print("FAILURE: Gemini API is not working.")