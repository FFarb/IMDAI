@echo off
cd image-prompt-app\backend
python -m venv venv
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate
    pip install -r requirements.txt
    if not exist ".env" copy .env.example .env >nul
    deactivate
)
cd ..\frontend
npm install
cd ..
echo Setup complete
