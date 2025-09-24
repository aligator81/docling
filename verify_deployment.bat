@echo off
echo ========================================================
echo 🔍 Coolify Deployment Verification Tool
echo ========================================================
echo.

set /p SERVER_IP="Enter your Coolify server IP address: "

echo.
echo 📊 Checking deployment status...
echo ================================
echo.

echo 1. Testing application accessibility...
curl -s -o nul -w "%%{http_code}" "http://%SERVER_IP%:8501/"
if errorlevel 1 (
    echo ❌ Cannot connect to application
    echo   Check if server IP is correct and port 8501 is open
) else (
    echo ✅ Application is accessible at http://%SERVER_IP%:8501
)

echo.
echo 2. Testing health check endpoint...
curl -s -o nul -w "%%{http_code}" "http://%SERVER_IP%:8501/_stcore/health"
if errorlevel 1 (
    echo ❌ Health check failed
) else (
    echo ✅ Health check passed
)

echo.
echo 3. Quick functional test...
curl -s "http://%SERVER_IP%:8501" | findstr "Streamlit" >nul
if errorlevel 1 (
    echo ⚠️  Streamlit interface not detected
) else (
    echo ✅ Streamlit interface detected
)

echo.
echo 📋 Manual Verification Steps:
echo =============================
echo.
echo A. Coolify Dashboard Checks:
echo   1. Go to your project → Deployments tab
echo   2. Look for ✅ Green checkmark = Success
echo   3. Check logs for "Build successful"
echo.
echo B. Application Functional Tests:
echo   1. Open http://%SERVER_IP%:8501 in browser
echo   2. Should see API configuration screen
echo   3. No Python errors should appear
echo.
echo C. Feature Testing:
echo   1. Configure API keys (test with dummy values)
echo   2. Try uploading a test document
echo   3. Check if sidebar loads correctly
echo.
echo 🚨 Common Issues:
echo ================
echo - Connection refused: Check firewall/port 8501
echo - Python errors: Check application logs in Coolify
echo - Build failed: Review deployment logs
echo - Memory issues: Increase resources in Coolify
echo.
echo 🔧 Next Steps if Issues Found:
echo =============================
echo 1. Check Coolify deployment logs
echo 2. Verify environment variables are set
echo 3. Test database connection
echo 4. Monitor resource usage
echo.
echo ✅ Success Indicators:
echo =====================
echo - Application loads without errors
echo - All features functional
echo - Stable resource usage
echo - No crashes in logs
echo.
pause