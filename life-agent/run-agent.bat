@echo off
echo ================================
echo Life Agent - Simple Start
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed!
    echo.
    echo Download Python from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit
)

echo Installing dependencies...
pip install python-telegram-bot anthropic python-dotenv sqlalchemy pyyaml python-dateutil pytz --quiet

echo.
echo ================================
echo Enter Your API Keys
echo ================================
echo.

set /p TELEGRAM_TOKEN="Telegram Bot Token: "
set /p ANTHROPIC_KEY="Anthropic API Key: "

echo.
echo Creating configuration...

echo TELEGRAM_BOT_TOKEN=%TELEGRAM_TOKEN%> .env
echo ANTHROPIC_API_KEY=%ANTHROPIC_KEY%>> .env
echo DATABASE_URL=sqlite:///data/lifeagent.db>> .env
echo TIMEZONE=America/Chicago>> .env
echo LOG_LEVEL=INFO>> .env

if not exist data mkdir data
if not exist logs mkdir logs

echo.
echo ================================
echo Starting Life Agent...
echo ================================
echo.

python main.py

pause
