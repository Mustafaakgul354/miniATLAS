#!/bin/bash
# Startup script for mini-Atlas Desktop (macOS/Linux)

echo "Starting mini-Atlas Desktop..."

# Check if backend is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "⚠️  Backend not running. Starting backend..."
    echo "Please start backend in another terminal:"
    echo "  uvicorn app.main:app --port 8000"
    echo ""
    read -p "Press Enter to continue anyway..."
fi

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Start Electron app
echo "🚀 Launching desktop app..."
npm start

