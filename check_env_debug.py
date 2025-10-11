import os

# Check the exact ALLOWED_EXTENSIONS value from environment
env_value = os.getenv("ALLOWED_EXTENSIONS")
print(f"Raw env value: {repr(env_value)}")
print(f"Length: {len(env_value) if env_value else 0}")

if env_value:
    # Check for any non-printable characters
    for i, char in enumerate(env_value):
        if ord(char) < 32 or ord(char) > 126:  # Non-printable ASCII
            print(f"Non-printable char at position {i}: {ord(char)}")

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