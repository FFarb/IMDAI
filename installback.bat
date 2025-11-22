@echo off
setlocal enabledelayedexpansion

echo ===============================
echo   Setting up Backend
echo ===============================

cd backend

REM Create venv if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Python requirements...
pip install -r requirements.txt

if exist ".env" (
  echo .env already exists
) else (
  echo Copying .env.example to .env
  copy .env.example .env
)

echo ===============================
echo   Backend Setup Complete
echo ===============================
pause
