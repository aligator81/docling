import os

# Check the exact ALLOWED_EXTENSIONS value from environment when running from backend directory
env_value = os.getenv("ALLOWED_EXTENSIONS")
print(f"Raw env value: {repr(env_value)}")
print(f"Length: {len(env_value) if env_value else 0}")

if env_value:
    # Check if it's valid JSON
    import json
    try:
        parsed = json.loads(env_value)
        print(f"Parsed successfully: {parsed}")

        # Check for any anomalies in the parsed list
        for i, item in enumerate(parsed):
            print(f"  {i}: {repr(item)} (length: {len(item)})")

    except json.JSONDecodeError as e:
        print(f"❌ JSON decode error: {e}")
        print(f"Error position: {e.pos if hasattr(e, 'pos') else 'unknown'}")
        print("This means the .env file has malformed JSON!")