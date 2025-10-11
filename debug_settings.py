#!/usr/bin/env python3

import sys
import os

# Add backend to path
sys.path.append('backend')

# Test the settings configuration
try:
    from app.config import settings

    print("🔍 Current Settings Debug:")
    print(f"ALLOWED_EXTENSIONS env var: {os.getenv('ALLOWED_EXTENSIONS')}")
    print(f"Settings allowed_extensions: {settings.allowed_extensions}")
    print(f"Type: {type(settings.allowed_extensions)}")
    print(f"Length: {len(settings.allowed_extensions)}")

    # Test if .png is in the list
    png_in_list = '.png' in settings.allowed_extensions
    print(f".png in allowed_extensions: {png_in_list}")

    # Check the exact string representation
    extensions_str = ', '.join(settings.allowed_extensions)
    print(f"Extensions as string: {extensions_str}")

except Exception as e:
    print(f"❌ Error importing settings: {e}")
    import traceback
    traceback.print_exc()