@echo off
echo ==========================================
echo   IMDAI Mac Package Creator
echo ==========================================
echo.

echo Creating ZIP package for Mac...
echo.

REM Delete old ZIP if exists
if exist "IMDAI-Mac-Installer.zip" (
    echo Removing old ZIP file...
    del "IMDAI-Mac-Installer.zip"
)

echo.
echo Compressing files...
echo This may take a minute...
echo.

REM Use PowerShell to create ZIP
powershell -Command "Compress-Archive -Path 'backend','frontend','data','Setup IMDAI.command','INSTALLATION_INSTRUCTIONS.txt','README.md' -DestinationPath 'IMDAI-Mac-Installer.zip' -CompressionLevel Optimal -Force"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==========================================
    echo   Package Created Successfully!
    echo ==========================================
    echo.
    echo File: IMDAI-Mac-Installer.zip
    echo Location: %CD%
    echo.
    echo What to do next:
    echo 1. Send IMDAI-Mac-Installer.zip to your Mac user
    echo 2. Tell them to extract it
    echo 3. Tell them to double-click "Setup IMDAI.command"
    echo.
    echo Opening folder...
    explorer /select,"IMDAI-Mac-Installer.zip"
) else (
    echo.
    echo ERROR: Failed to create ZIP file!
    echo Please make sure all required files exist.
    echo.
)

echo.
pause
