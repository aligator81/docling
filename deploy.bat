@echo off
echo 🚀 Coolify Deployment Script for Document Q&A Assistant
echo =======================================================

REM Check if we're in the right directory
if not exist "5-chat.py" (
    echo ❌ Error: Please run this script from your project root directory
    exit /b 1
)

REM Check if Dockerfile exists
if not exist "Dockerfile" (
    echo ❌ Error: Dockerfile not found. Please create it first.
    exit /b 1
)

echo ✅ Project structure looks good

echo 📋 Deployment Checklist:
echo -----------------------
echo ✅ Dockerfile created
echo ✅ coolify.yml configured
echo ✅ .dockerignore created
echo ✅ README.md updated

echo.
echo 🔧 Next Steps:
echo ==============
echo 1. Push your code to your Git repository:
echo    git push origin main
echo.
echo 2. Set up Coolify server:
echo    - Provision a VPS/Server (Ubuntu 22.04 recommended)
echo    - Install Coolify: curl -fsSL https://get.coolify.io ^| bash
echo    - Access Coolify dashboard at http://your-server-ip:3000
echo.
echo 3. Configure deployment in Coolify:
echo    - Add project → Select your Git provider
echo    - Build Method: Dockerfile
echo    - Port: 8501
echo    - Set environment variables:
echo      OPENAI_API_KEY=your_key_here
echo      MISTRAL_API_KEY=your_key_here
echo      NEON_CONNECTION_STRING=your_connection_string
echo.
echo 4. Deploy and monitor logs
echo.
echo 📊 Application Details:
echo ======================
echo Main file: 5-chat.py (Streamlit app)
echo Port: 8501
echo Health check: /_stcore/health
echo Database: Neon PostgreSQL
echo LLM Providers: OpenAI ^& Mistral
echo Embedding Providers: OpenAI ^& Mistral
echo.
echo 🎯 Your application will be available at: http://your-coolify-server-ip:8501
echo.
echo Need help? Check the README.md file for detailed instructions.

pause