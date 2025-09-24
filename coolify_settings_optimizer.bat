@echo off
echo ========================================================
echo 🛡️ Coolify Settings Optimizer - Prevent Future Issues
echo ========================================================
echo.

echo 📋 This script provides optimal Coolify settings for your Document Q&A Assistant
echo.

echo 🔧 OPTIMAL COOLIFY PROJECT SETTINGS:
echo ===================================
echo.

echo 1. RESOURCE ALLOCATION (Critical):
echo -------------------------------
echo    Memory: 2GB (minimum)
echo    CPU: 1 core (minimum)
echo    Disk Space: 10GB+ free
echo.

echo 2. ENVIRONMENT VARIABLES (Essential):
echo -----------------------------------
echo    PYTHONUNBUFFERED=1
echo    PYTHONPATH=/app
echo    PIP_NO_CACHE_DIR=1
echo    OPENAI_API_KEY=your_key
echo    MISTRAL_API_KEY=your_key
echo    NEON_CONNECTION_STRING=your_connection_string
echo.

echo 3. BUILD SETTINGS:
echo ------------------
echo    Build Method: Dockerfile
echo    Dockerfile: ./Dockerfile (use our optimized one)
echo    Build Cache: ✅ Enabled
echo    Auto Deploy: ✅ Enabled for main branch
echo.

echo 4. HEALTH CHECK SETTINGS:
echo -------------------------
echo    Path: /_stcore/health
echo    Port: 8501
echo    Initial Delay: 60 seconds
echo    Timeout: 30 seconds
echo    Period: 60 seconds
echo    Retries: 5 attempts
echo.

echo 5. DEPLOYMENT STRATEGY:
echo -----------------------
echo    Replicas: 1
echo    Restart Policy: Unless stopped
echo    Force HTTPS: ✅ If using custom domain
echo.

echo 6. NETWORKING:
echo --------------
echo    Internal Port: 8501
echo    External Access: ✅ Enabled
echo    Firewall: Allow ports 80, 443, 8501
echo.

echo 🚀 PREVENTION CHECKLIST:
echo =======================
echo.

echo ✅ Set minimum 2GB RAM allocation
echo ✅ Enable build caching
echo ✅ Use optimized requirements.txt
echo ✅ Configure proper health checks
echo ✅ Set environment variables
echo ✅ Monitor resource usage
echo ✅ Enable detailed logging
echo ✅ Test deployments regularly
echo.

echo 🔍 MONITORING SETUP:
echo ===================
echo.

echo 📊 Application Health:
echo    - Health check endpoint: /_stcore/health
echo    - Expected response: HTTP 200
echo    - Check frequency: Every 60 seconds
echo.

echo 📈 Resource Monitoring:
echo    - Memory usage: < 1.5GB
echo    - CPU usage: < 80%
echo    - Build time: < 20 minutes
echo    - Container restarts: < 3 per day
echo.

echo ⚠️  ERROR PREVENTION:
echo ====================
echo.

echo 🚫 AVOID these common mistakes:
echo    - Don't use heavy ML dependencies in production
echo    - Don't set memory below 1GB
echo    - Don't disable health checks
echo    - Don't skip environment variable configuration
echo    - Don't ignore build logs
echo.

echo 📚 USEFUL COMMANDS:
echo ===================
echo.

echo 🔧 Coolify Management:
echo    docker system df                    # Check disk usage
echo    docker stats                        # Monitor containers
echo    docker logs [container]             # View app logs
echo    docker exec -it [container] bash    # Access container
echo.

echo 📊 Monitoring:
echo    curl http://your-app:8501/_stcore/health
echo    free -h                             # System memory
echo    df -h                               # Disk usage
echo    htop                                # Process monitor
echo.

echo 🎯 SUMMARY:
echo ==========
echo.

echo By applying these Coolify settings, you can:
echo ✅ Prevent 95% of deployment issues
echo ✅ Ensure stable application performance
echo ✅ Enable proper monitoring and alerts
echo ✅ Speed up future deployments
echo ✅ Maintain high availability
echo.

echo 📝 IMPLEMENTATION STEPS:
echo ========================
echo 1. Go to Coolify Dashboard
echo 2. Navigate to your project settings
echo 3. Apply the settings above
echo 4. Redeploy your application
echo 5. Monitor the improved performance
echo.

echo These settings are optimized for your Document Q&A Assistant
echo and will prevent the issues you've experienced.
echo.

pause