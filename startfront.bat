@echo off
setlocal enabledelayedexpansion

echo ===============================
echo   Starting Frontend Server
echo ===============================

cd frontend
npm run dev

echo ===============================
echo   Frontend server launched
echo ===============================
pause
