@echo off
REM Start script for Dark Web OSINT Web Interface (Windows)

echo ╔════════════════════════════════════════════════════════════╗
echo ║                                                            ║
echo ║     🕵️  Dark Web OSINT Automation Dashboard               ║
echo ║                                                            ║
echo ║     Starting Professional Minimalist Interface...         ║
echo ║                                                            ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ Error: app.py not found!
    echo Please run this script from the web_interface directory
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔌 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo 📥 Installing dependencies...
pip install -q -r requirements.txt

REM Create necessary directories
if not exist "..\logs" mkdir ..\logs
if not exist "..\output" mkdir ..\output

echo.
echo ✅ Setup complete!
echo.
echo 🚀 Starting Flask server on http://localhost:8080
echo.
echo Press Ctrl+C to stop
echo ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
echo.

REM Start the Flask app
python app.py

pause
