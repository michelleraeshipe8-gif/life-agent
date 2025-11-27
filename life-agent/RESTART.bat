@echo off
echo ========================================
echo FIXING AND RESTARTING LIFE AGENT
echo ========================================
echo.

cd /d "%~dp0"

REM Stop any running Python processes
echo Stopping agent...
taskkill /F /IM python.exe 2>nul

REM Wait a moment
timeout /t 2 /nobreak >nul

echo.
echo Starting fixed agent...
echo.

python main.py

pause
