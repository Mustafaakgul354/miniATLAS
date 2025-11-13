@echo off
REM Startup script for mini-Atlas Desktop (Windows)

echo Starting mini-Atlas Desktop...

REM Check if backend is running
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Backend not running. Please start backend first:
    echo   uvicorn app.main:app --port 8000
    echo.
    pause
)

REM Check if node_modules exists
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

REM Start Electron app
echo 🚀 Launching desktop app...
call npm start

