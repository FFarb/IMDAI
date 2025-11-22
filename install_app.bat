@echo off
echo ===============================
echo   Installing Full Application
echo ===============================

echo.
echo [1/2] Installing Backend...
call installback.bat

echo.
echo [2/2] Installing Frontend...
call installfront.bat

echo.
echo ===============================
echo   Full Installation Complete!
echo ===============================
pause
