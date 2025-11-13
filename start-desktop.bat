@echo off
REM Startup script for mini-Atlas Desktop Application (Windows)

echo Starting mini-Atlas Desktop Application...
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Node.js is not installed. Please install Node.js 16 or higher.
    pause
    exit /b 1
)

REM Check if npm dependencies are installed
if not exist "node_modules" (
    echo Installing Node.js dependencies...
    call npm install
    if %ERRORLEVEL% NEQ 0 (
        echo Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check if Python backend is running
echo Checking Python backend...
curl -s http://localhost:8000/health >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Python backend is running
) else (
    echo WARNING: Python backend is not running!
    echo.
    echo Please start the backend in a separate terminal:
    echo   cd %CD%
    echo   .venv\Scripts\activate
    echo   uvicorn app.main:app --host 0.0.0.0 --port 8000
    echo.
    echo Press any key to continue anyway, or Ctrl+C to cancel...
    pause >nul
)

REM Start Electron app
echo Launching desktop application...
npm start
