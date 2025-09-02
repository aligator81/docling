#!/usr/bin/env python3

# Quick test to reproduce the exact error scenario
import os
from openai import OpenAI
from dotenv import load_dotenv

print("=== Quick OpenAI Test ===")

# First, try without loading .env (this should fail)
print("\n1. Testing without load_dotenv():")
try:
    client = OpenAI()
    print("✅ Success: OpenAI client created without explicit .env loading")
except Exception as e:
    print(f"❌ Error: {e}")

# Now test with load_dotenv()
print("\n2. Testing with load_dotenv():")
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
print(f"   API key found: {api_key is not None}")

try:
    client = OpenAI()  # Should work now
    print("✅ Success: OpenAI client created after load_dotenv()")
except Exception as e:
    print(f"❌ Error: {e}")

# Test with explicit API key (current 5-chat.py approach)
print("\n3. Testing with explicit api_key parameter:")
if api_key:
    try:
        client = OpenAI(api_key=api_key)
        print("✅ Success: OpenAI client created with explicit api_key")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ No API key available for testing")

print("\n=== Test Complete ===")