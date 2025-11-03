@echo off
start "Backend" cmd /k "cd image-prompt-app\backend && call venv\Scripts\activate && uvicorn app:app --reload"
start "Frontend" cmd /k "cd image-prompt-app\frontend && npm run dev"
