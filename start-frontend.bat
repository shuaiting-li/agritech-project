@echo off
REM Startup script for Cresco frontend

echo ========================================
echo Starting Cresco Frontend
echo ========================================

REM Navigate to brontend directory
cd brontend

REM Check if node_modules exists
if not exist node_modules (
    echo Installing dependencies...
    call npm install
)

echo.
echo Starting Vite dev server on http://localhost:5173
echo Press Ctrl+C to stop
echo.

REM Run the development server
call npm run dev

pause
