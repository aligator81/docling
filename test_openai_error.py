#!/usr/bin/env python3

# This script reproduces the original error to help diagnose the issue

import os
from openai import OpenAI
from dotenv import load_dotenv

print("Testing OpenAI client initialization...")

# Test 1: Without loading .env (original error scenario)
print("\n=== Test 1: Without .env loading ===")
try:
    client = OpenAI()  # This should reproduce the original error
    print("✅ OpenAI client created successfully without explicit API key")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: With .env loading but no explicit API key
print("\n=== Test 2: With .env loading but no explicit API key ===")
load_dotenv()
try:
    client = OpenAI()  # This should work if env var is loaded
    print("✅ OpenAI client created successfully after loading .env")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: With explicit API key (current 5-chat.py approach)
print("\n=== Test 3: With explicit API key ===")
api_key = os.getenv("OPENAI_API_KEY")
print(f"API key loaded: {api_key is not None}")
if api_key:
    print(f"API key length: {len(api_key)}")
    print(f"API key starts with sk-: {api_key.startswith('sk-')}")
    try:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client created successfully with explicit API key")
    except Exception as e:
        print(f"❌ Error: {e}")
else:
    print("❌ No API key found in environment variables")