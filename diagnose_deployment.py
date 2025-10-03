#!/usr/bin/env python3
"""
Deployment Diagnostic Script for Coolify
Run this script in your Coolify container to identify issues
"""

import os
import sys
import psycopg2
from openai import OpenAI
from mistralai import Mistral
from dotenv import load_dotenv

def print_status(service, status, message=""):
    """Print formatted status message"""
    icon = "✅" if status else "❌"
    print(f"{icon} {service}: {'Working' if status else 'Failed'} {message}")

def check_environment_variables():
    """Check if all required environment variables are set"""
    print("🔍 Checking Environment Variables...")
    
    required_vars = [
        'NEON_CONNECTION_STRING',
        'OPENAI_API_KEY', 
        'MISTRAL_API_KEY',
        'EMBEDDING_PROVIDER'
    ]
    
    all_set = True
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: SET")
            # Show first few characters for verification
            if 'KEY' in var or 'STRING' in var:
                print(f"      Value: {value[:20]}...")
        else:
            print(f"   ❌ {var}: NOT SET")
            all_set = False
    
    return all_set

def check_database_connection():
    """Test Neon database connection"""
    print("\n🗄️ Testing Database Connection...")
    
    connection_string = os.getenv('NEON_CONNECTION_STRING')
    if not connection_string:
        print("   ❌ No connection string found")
        return False
    
    try:
        conn = psycopg2.connect(connection_string)
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"   ✅ Database connected: {version.split(',')[0]}")
        
        # Check if required tables exist
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('documents', 'document_chunks', 'embeddings')
            """)
            tables = [row[0] for row in cur.fetchall()]
            print(f"   📊 Found tables: {', '.join(tables) if tables else 'None'}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        return False

def check_openai_connection():
    """Test OpenAI API connection"""
    print("\n🤖 Testing OpenAI API...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("   ❌ OpenAI API key not set")
        return False
    
    try:
        client = OpenAI(api_key=api_key)
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'Hello'"}],
            max_tokens=5
        )
        print(f"   ✅ OpenAI API working: {response.choices[0].message.content.strip()}")
        return True
    except Exception as e:
        print(f"   ❌ OpenAI API failed: {e}")
        return False

def check_mistral_connection():
    """Test Mistral API connection"""
    print("\n🌪️ Testing Mistral API...")
    
    api_key = os.getenv('MISTRAL_API_KEY')
    if not api_key:
        print("   ❌ Mistral API key not set")
        return False
    
    try:
        client = Mistral(api_key=api_key)
        # Test with embeddings instead of chat (more reliable)
        response = client.embeddings.create(
            model="mistral-embed",
            inputs=["Hello"]
        )
        print(f"   ✅ Mistral API working: Embeddings created successfully")
        return True
    except Exception as e:
        print(f"   ❌ Mistral API failed: {e}")
        print(f"   💡 Note: This might be a version compatibility issue")
        return False

def check_embedding_provider():
    """Check if embedding provider is configured correctly"""
    print("\n🧬 Checking Embedding Provider...")
    
    provider = os.getenv('EMBEDDING_PROVIDER', 'openai')
    print(f"   📋 Configured provider: {provider}")
    
    if provider == 'openai':
        return check_openai_connection()
    elif provider == 'mistral':
        return check_mistral_connection()
    else:
        print(f"   ❌ Unknown embedding provider: {provider}")
        return False

def check_file_permissions():
    """Check if required directories exist and have proper permissions"""
    print("\n📁 Checking File Permissions...")
    
    required_dirs = ['data/uploads', 'output', 'cache']
    all_ok = True
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            if os.access(dir_path, os.W_OK):
                print(f"   ✅ {dir_path}: Exists and writable")
            else:
                print(f"   ❌ {dir_path}: Exists but not writable")
                all_ok = False
        else:
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"   ✅ {dir_path}: Created successfully")
            except Exception as e:
                print(f"   ❌ {dir_path}: Failed to create - {e}")
                all_ok = False
    
    return all_ok

def main():
    """Run all diagnostic checks"""
    print("🚀 Coolify Deployment Diagnostic Tool")
    print("=" * 50)
    
    # Load .env for local development (won't affect Coolify)
    load_dotenv()
    
    # Run all checks
    checks = [
        ("Environment Variables", check_environment_variables()),
        ("Database Connection", check_database_connection()),
        ("OpenAI API", check_openai_connection()),
        ("Mistral API", check_mistral_connection()),
        ("Embedding Provider", check_embedding_provider()),
        ("File Permissions", check_file_permissions())
    ]
    
    print("\n" + "=" * 50)
    print("📊 DIAGNOSTIC SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for service, status in checks:
        print_status(service, status)
        if not status:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL SYSTEMS GO! Your deployment should be working correctly.")
        print("💡 If chat still doesn't work, check the application logs for specific errors.")
    else:
        print("🔧 DEPLOYMENT ISSUES DETECTED")
        print("💡 Fix the issues above and redeploy your application.")
        print("📖 See COOLIFY_DEPLOYMENT_TROUBLESHOOTING.md for solutions.")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())