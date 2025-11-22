@echo off
setlocal enabledelayedexpansion

echo ===============================
echo   Starting Frontend Server
echo ===============================

cd frontend
if not exist "node_modules" (
    echo Error: node_modules not found.
    echo Please run installfront.bat first.
    pause
    exit /b 1
)

call npm run dev

echo ===============================
echo   Frontend server stopped
echo ===============================
pause
