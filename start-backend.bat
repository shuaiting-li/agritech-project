@echo off
REM Startup script for Cresco backend

echo ========================================
echo Starting Cresco Backend
echo ========================================

REM Check if .env exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create .env file with Azure OpenAI credentials
    echo See .env.example for reference
    pause
    exit /b 1
)

REM Navigate to src directory
cd src

echo.
echo Starting FastAPI server on http://localhost:8000
echo Press Ctrl+C to stop
echo.

REM Run the application
python -m cresco.main

pause
