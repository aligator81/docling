@echo off
echo ========================================================
echo 🚀 GitHub Repository Creation Helper
echo ========================================================
echo.

echo 📊 Current Repository Status:
echo ----------------------------
git remote -v
echo.

echo 📋 Your current repository is connected to:
echo    https://github.com/aligator81/docling.git
echo.

echo 🔧 Options:
echo ----------
echo 1. Use existing repository (recommended for Coolify)
echo 2. Create new repository
echo.

set /p choice="Choose option (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo ✅ Great! Your project is already on GitHub.
    echo.
    echo 🎯 Next steps for Coolify deployment:
    echo   1. Go to https://github.com/aligator81/docling
    echo   2. Verify all files are present
    echo   3. Set up Coolify server
    echo   4. Connect Coolify to your GitHub repository
    echo.
    echo 📚 Repository URL: https://github.com/aligator81/docling
)

if "%choice%"=="2" (
    echo.
    echo 📝 To create a new GitHub repository:
    echo.
    echo 1. Go to https://github.com/new
    echo 2. Fill in repository details:
    echo    - Owner: aligator81
    echo    - Repository name: [choose-new-name]
    echo    - Description: Document Q&A Assistant with Coolify deployment
    echo    - Public/Private: Choose as needed
    echo    - Initialize with README: No (you already have one)
    echo.
    echo 3. After creating the repository, run these commands:
    echo    git remote rename origin old-origin
    echo    git remote add origin https://github.com/aligator81/[new-repo-name].git
    echo    git push -u origin main
    echo.
    echo ⚠️  Note: Creating a new repo will break Coolify connection if already set up.
)

echo.
echo 📁 Current project files ready for deployment:
echo   - Dockerfile ✅
echo   - coolify.yml ✅  
echo   - README.md ✅
echo   - Deployment scripts ✅
echo.
echo 🎉 Your Document Q&A Assistant is deployment-ready!
pause