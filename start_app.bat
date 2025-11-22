@echo off
echo ===============================
echo   Starting Full Application
echo ===============================

echo Starting Backend...
start "Backend Server" startback.bat

echo Starting Frontend...
start "Frontend Server" startfront.bat

echo.
echo Application started in separate windows.
