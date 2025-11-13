#!/bin/bash
# Startup script for mini-Atlas Desktop Application

echo "🚀 Starting mini-Atlas Desktop Application..."
echo ""

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16 or higher."
    exit 1
fi

# Check if npm dependencies are installed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check if Python backend is running
echo "🔍 Checking Python backend..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Python backend is running"
else
    echo "⚠️  Python backend is not running!"
    echo ""
    echo "Please start the backend in a separate terminal:"
    echo "  cd $(pwd)"
    echo "  source .venv/bin/activate  # or .venv\\Scripts\\activate on Windows"
    echo "  uvicorn app.main:app --host 0.0.0.0 --port 8000"
    echo ""
    echo "Press Ctrl+C to cancel, or wait 5 seconds to continue anyway..."
    sleep 5
fi

# Start Electron app
echo "🖥️  Launching desktop application..."
npm start
