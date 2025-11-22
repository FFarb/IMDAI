@echo off
setlocal enabledelayedexpansion

echo ===============================
echo   Starting Backend Server
echo ===============================

cd backend
if not exist "venv" (
    echo Virtual environment not found! Please run installback.bat first.
    pause
    exit /b 1
)

call venv\Scripts\activate
uvicorn app:app --reload

echo ===============================
echo   Backend server stopped
echo ===============================
pause
