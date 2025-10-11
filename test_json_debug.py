import json

# Test the JSON parsing
test_json = '["pdf","docx","md","html","png","jpg","jpeg","tiff","bmp","txt","rtf"]'

print(f"Original string: {test_json}")
print(f"Length: {len(test_json)}")

try:
    parsed = json.loads(test_json)
    print(f"Parsed: {parsed}")
    print(f"Length of parsed: {len(parsed)}")

    # Check each item
    for i, item in enumerate(parsed):
        print(f"  {i}: '{item}'")

except Exception as e:
    print(f"❌ JSON parsing error: {e}")

# Test character by character
print("\nCharacter analysis:")
for i, char in enumerate(test_json):
    print(f"  {i}: '{char}' ({ord(char)})")