#!/usr/bin/env python3
"""
Quick Deployment Fix for Coolify
Run this script in your Coolify container to fix common deployment issues
"""

import os
import sys
import subprocess
import psycopg2
from dotenv import load_dotenv

def run_command(cmd, description):
    """Run a command and print status"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {description} completed")
            return True
        else:
            print(f"   ❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"   ❌ {description} error: {e}")
        return False

def fix_environment_variables():
    """Ensure environment variables are properly loaded"""
    print("\n🔧 Fixing Environment Variables...")
    
    # Check if we're in a container environment
    if os.path.exists('/.dockerenv'):
        print("   📦 Running in Docker container")
    
    # List all environment variables (without values for security)
    env_vars = ['NEON_CONNECTION_STRING', 'OPENAI_API_KEY', 'MISTRAL_API_KEY', 'EMBEDDING_PROVIDER']
    for var in env_vars:
        if os.getenv(var):
            print(f"   ✅ {var}: SET")
        else:
            print(f"   ❌ {var}: NOT SET - This will cause issues!")
    
    return all(os.getenv(var) for var in env_vars)

def fix_database_connection():
    """Fix common database connection issues"""
    print("\n🔧 Fixing Database Connection...")
    
    connection_string = os.getenv('NEON_CONNECTION_STRING')
    if not connection_string:
        print("   ❌ No database connection string found")
        return False
    
    try:
        # Test connection
        conn = psycopg2.connect(connection_string)
        
        # Check if pgvector extension is installed
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector'")
            if not cur.fetchone():
                print("   ⚠️ pgvector extension not found - installing...")
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                conn.commit()
                print("   ✅ pgvector extension installed")
            else:
                print("   ✅ pgvector extension already installed")
        
        # Check if required tables exist
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_name IN ('documents', 'document_chunks', 'embeddings')
            """)
            existing_tables = [row[0] for row in cur.fetchall()]
            
            required_tables = ['documents', 'document_chunks', 'embeddings']
            missing_tables = [t for t in required_tables if t not in existing_tables]
            
            if missing_tables:
                print(f"   ⚠️ Missing tables: {missing_tables}")
                print("   💡 You need to run the database setup scripts")
            else:
                print("   ✅ All required tables exist")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        print("   💡 Check your NEON_CONNECTION_STRING and database permissions")
        return False

def fix_file_permissions():
    """Ensure required directories exist and have proper permissions"""
    print("\n🔧 Fixing File Permissions...")
    
    required_dirs = ['data/uploads', 'output', 'cache']
    all_ok = True
    
    for dir_path in required_dirs:
        try:
            os.makedirs(dir_path, exist_ok=True)
            # Try to create a test file to check write permissions
            test_file = os.path.join(dir_path, '.test_write')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            print(f"   ✅ {dir_path}: Writable")
        except Exception as e:
            print(f"   ❌ {dir_path}: Not writable - {e}")
            all_ok = False
    
    return all_ok

def fix_python_dependencies():
    """Ensure all Python dependencies are installed"""
    print("\n🔧 Fixing Python Dependencies...")
    
    # First upgrade pip to avoid version issues
    print("   🔄 Upgrading pip...")
    subprocess.run("python -m pip install --upgrade pip", shell=True, capture_output=True)
    
    # Install core dependencies individually to handle failures gracefully
    core_dependencies = [
        "streamlit",
        "psycopg2-binary",  # Use binary version to avoid compilation
        "openai",
        "mistralai",
        "python-dotenv",
        "numpy",
        "pandas",
        "requests",
        "tiktoken",
        "sentence-transformers",
        "langchain",
        "langchain-openai",
        "langchain-mistralai",
        "langchain-community",
        "pypdf2",
        "python-multipart",
        "flask"
    ]
    
    all_success = True
    
    for dep in core_dependencies:
        try:
            print(f"   📦 Installing {dep}...")
            result = subprocess.run(
                f"pip install {dep}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            if result.returncode == 0:
                print(f"   ✅ {dep} installed successfully")
            else:
                print(f"   ⚠️ {dep} installation failed: {result.stderr[:200]}...")
                # Don't fail the whole process for one dependency
        except subprocess.TimeoutExpired:
            print(f"   ⚠️ {dep} installation timed out")
        except Exception as e:
            print(f"   ⚠️ {dep} installation error: {e}")
    
    # Try to install requirements.txt as fallback, but don't fail if it doesn't work
    if os.path.exists('requirements.txt'):
        print("   📦 Installing from requirements.txt...")
        success = run_command(
            "pip install -r requirements.txt --timeout 300",
            "Installing from requirements.txt"
        )
        if not success:
            print("   ⚠️ requirements.txt installation failed, but core dependencies should work")
    
    # Verify critical dependencies are installed
    critical_deps = {
        'streamlit': 'streamlit',
        'psycopg2-binary': 'psycopg2',  # psycopg2-binary imports as psycopg2
        'openai': 'openai'
    }
    missing_critical = []
    
    for dep_name, import_name in critical_deps.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_critical.append(dep_name)
    
    if missing_critical:
        print(f"   ❌ Missing critical dependencies: {missing_critical}")
        return False
    
    print("   ✅ Core dependencies installed successfully")
    return True

def create_health_check():
    """Create a simple health check endpoint"""
    print("\n🔧 Creating Health Check...")
    
    health_check_content = '''
import os
import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/health')
def health_check():
    status = {
        'status': 'healthy',
        'database': False,
        'openai': bool(os.getenv('OPENAI_API_KEY')),
        'mistral': bool(os.getenv('MISTRAL_API_KEY'))
    }
    
    # Test database connection
    try:
        conn = psycopg2.connect(os.getenv('NEON_CONNECTION_STRING'))
        conn.close()
        status['database'] = True
    except:
        status['database'] = False
    
    return jsonify(status)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
'''
    
    try:
        with open('health_check.py', 'w') as f:
            f.write(health_check_content)
        print("   ✅ Health check endpoint created")
        return True
    except Exception as e:
        print(f"   ❌ Failed to create health check: {e}")
        return False

def main():
    """Run all deployment fixes"""
    print("🚀 Quick Deployment Fix Tool")
    print("=" * 50)
    print("This script will attempt to fix common deployment issues.")
    print("Run this in your Coolify container if the chat isn't working.")
    print("=" * 50)
    
    # Load .env for local development
    load_dotenv()
    
    # Run all fixes
    fixes = [
        ("Environment Variables", fix_environment_variables()),
        ("Database Connection", fix_database_connection()),
        ("File Permissions", fix_file_permissions()),
        ("Python Dependencies", fix_python_dependencies()),
        ("Health Check", create_health_check())
    ]
    
    print("\n" + "=" * 50)
    print("📊 FIX SUMMARY")
    print("=" * 50)
    
    successful_fixes = sum(1 for _, status in fixes if status)
    total_fixes = len(fixes)
    
    for fix_name, status in fixes:
        icon = "✅" if status else "❌"
        print(f"{icon} {fix_name}")
    
    print(f"\n🎯 {successful_fixes}/{total_fixes} fixes applied successfully")
    
    if successful_fixes == total_fixes:
        print("\n🎉 All fixes applied successfully!")
        print("💡 Restart your application and test the chat functionality.")
    else:
        print("\n⚠️ Some fixes failed. Check the logs above for details.")
        print("💡 You may need to manually configure some settings in Coolify.")
    
    print("\n📖 Next steps:")
    print("1. Restart your application in Coolify")
    print("2. Check the application logs for any remaining errors")
    print("3. Test the chat functionality")
    print("4. Run diagnose_deployment.py to verify everything is working")
    
    return 0 if successful_fixes >= 3 else 1

if __name__ == "__main__":
    sys.exit(main())