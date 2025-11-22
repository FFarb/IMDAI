@echo off
setlocal enabledelayedexpansion

echo ===============================
echo   Setting up Backend
echo ===============================

cd backend
python -m venv venv
call venv\Scripts\activate

echo Installing Python requirements...
pip install -r requirements.txt

if exist ".env" (
  echo .env already exists
) else (
  echo Copying .env.example to .env
  copy .env.example .env
)

echo ===============================
echo   backend Setup Complete
echo ===============================
pause
