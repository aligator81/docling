@echo off
echo ========================================================
echo 🔧 Coolify GitHub Authentication Fix
echo ========================================================
echo.

echo ❌ Error Detected:
echo    "fatal: could not read Username for 'https://github.com': No such device or address"
echo.

echo 🔧 Solution 1: GitHub App Integration (Recommended)
echo ---------------------------------------------------
echo 1. Go to Coolify Dashboard → Settings → Source Control
echo 2. Click "Connect GitHub" 
echo 3. Authorize Coolify to access your repositories
echo 4. Go back to your project and redeploy
echo.

echo 🔧 Solution 2: Personal Access Token (Quick Fix)
echo ------------------------------------------------
echo 1. Create GitHub PAT: https://github.com/settings/tokens
echo 2. Required permissions: repo (full control)
echo 3. In Coolify project settings, update Git URL to:
echo    https://[YOUR_TOKEN]@github.com/aligator81/docling.git
echo.

echo 🔧 Solution 3: Make Repository Public (Easiest)
echo -----------------------------------------------
echo 1. Go to: https://github.com/aligator81/docling/settings
echo 2. Scroll down to "Danger Zone"
echo 3. Click "Change visibility" → Make public
echo 4. Coolify can now clone without authentication
echo.

echo 🔧 Solution 4: SSH Key Authentication
echo -------------------------------------
echo 1. On Coolify server: ssh-keygen -t ed25519
echo 2. Add public key to GitHub SSH keys
echo 3. Use SSH URL: git@github.com:aligator81/docling.git
echo.

echo 📋 Immediate Action Steps:
echo --------------------------
echo 1. Try Solution 3 first (make repo public) - fastest
echo 2. If keeping private, use Solution 1 (GitHub App)
echo 3. Test deployment after applying fix
echo.

echo 🔗 Useful Links:
echo ----------------
echo - GitHub PAT: https://github.com/settings/tokens
echo - Repository Settings: https://github.com/aligator81/docling/settings
echo - Coolify Docs: https://coolify.io/docs/source-control/github
echo.

echo ⚠️  Important: After applying any fix, redeploy your application in Coolify.
pause