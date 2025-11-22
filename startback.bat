@echo off
setlocal enabledelayedexpansion

echo ===============================
echo   Starting Backend Server
echo ===============================

cd backend
python -m venv venv
call venv\Scripts\activate
uvicorn app:app --reload"

echo ===============================
echo   Backend server launched
echo ===============================
pause
