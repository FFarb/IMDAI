@echo off
REM Deploy Update Script for IMDAI POD Merch Swarm
REM This script commits and pushes all changes to GitHub

echo ========================================
echo IMDAI - Deploying Updates to GitHub
echo ========================================
echo.

REM Step 1: Checkout main branch
echo [1/5] Checking out main branch...
git checkout main
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to checkout main branch
    pause
    exit /b 1
)
echo.

REM Step 2: Add all changes
echo [2/5] Adding all changes...
git add .
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to add changes
    pause
    exit /b 1
)
echo.

REM Step 3: Commit changes
echo [3/5] Committing changes...
git commit -m "Refactor: Fixed OpenAI client, added Trend Agent & Background Removal"
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Nothing to commit or commit failed
    echo Continuing anyway...
)
echo.

REM Step 4: Push to GitHub
echo [4/5] Pushing to GitHub (origin main)...
git push origin main
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to push to GitHub
    echo Please check your network connection and GitHub credentials
    pause
    exit /b 1
)
echo.

REM Step 5: Success
echo [5/5] Update pushed to GitHub successfully!
echo ========================================
echo.
echo All changes have been deployed to:
echo https://github.com/FFarb/IMDAI
echo.
echo Press any key to exit...
pause >nul
