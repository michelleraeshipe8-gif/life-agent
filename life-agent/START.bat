@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ================================
echo Life Agent - AUTOMATIC SETUP
echo ================================
echo.
echo This will set up everything automatically.
echo.

REM Install Python packages
echo [1/5] Installing dependencies...
pip install python-telegram-bot anthropic python-dotenv sqlalchemy pyyaml python-dateutil pytz playwright --quiet
if errorlevel 1 (
    echo ERROR: Failed to install packages. Make sure Python is installed.
    pause
    exit /b 1
)
echo DONE
echo.

REM Create directories
echo [2/5] Creating directories...
if not exist logs mkdir logs
if not exist data mkdir data
if not exist data\uploads mkdir data\uploads
if not exist data\screenshots mkdir data\screenshots
echo DONE
echo.

REM Fix code bugs
echo [3/5] Fixing code...
powershell -Command "(Get-Content core\models.py) -replace 'metadata = Column', 'meta_data = Column' | Set-Content core\models.py" 2>nul
echo DONE
echo.

REM Get API keys
echo [4/5] Configuration...
if not exist .env (
    echo.
    echo Enter your API keys:
    set /p TELEGRAM_TOKEN="Telegram Bot Token: "
    set /p ANTHROPIC_KEY="Anthropic API Key: "
    
    (
        echo TELEGRAM_BOT_TOKEN=!TELEGRAM_TOKEN!
        echo ANTHROPIC_API_KEY=!ANTHROPIC_KEY!
        echo DATABASE_URL=sqlite:///data/lifeagent.db
        echo TIMEZONE=America/Chicago
        echo LOG_LEVEL=INFO
        echo ENABLE_BROWSER_AUTOMATION=false
        echo MAX_MEMORY_MESSAGES=100
    ) > .env
    echo Configuration saved to .env
) else (
    echo Configuration already exists (.env file found)
)
echo DONE
echo.

REM Start agent
echo [5/5] Starting Life Agent...
echo.
echo ================================
echo LIFE AGENT IS STARTING...
echo ================================
echo.
echo Press Ctrl+C to stop
echo.

python main.py

if errorlevel 1 (
    echo.
    echo ================================
    echo ERROR OCCURRED
    echo ================================
    echo.
    echo Check the error message above.
    echo.
    pause
    exit /b 1
)

pause
