@echo off
setlocal enabledelayedexpansion

echo ===============================
echo   Setting up Frontend
echo ===============================

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: npm is not installed or not in PATH.
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

cd frontend
call npm install

echo ===============================
echo   Frontend Setup Complete
echo ===============================
pause
