import os
from dotenv import load_dotenv

print('=== Environment Variable Test ===')
print(f'.env file exists: {os.path.exists(".env")}')

# Test without loading .env
api_key_before = os.getenv('OPENAI_API_KEY')
print(f'API key before load_dotenv: {api_key_before is not None}')

# Load .env
load_dotenv()
api_key_after = os.getenv('OPENAI_API_KEY')
print(f'API key after load_dotenv: {api_key_after is not None}')

if api_key_after:
    print(f'API key length: {len(api_key_after)}')
    print(f'API key starts with sk-: {api_key_after.startswith("sk-")}')
    
    # Test OpenAI client creation
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key_after)
        print('✅ OpenAI client created successfully!')
    except Exception as e:
        print(f'❌ OpenAI client error: {e}')
else:
    print('❌ No API key found')