#!/bin/bash

echo "🚀 Starting Friend Minder Application..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed or not in PATH"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    echo "❌ Error: node is not installed or not in PATH"
    exit 1
fi

# Setup backend
echo "📦 Setting up backend..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install backend dependencies
echo "Installing backend dependencies..."
pip install -r requirements.txt

# Check for Google Calendar credentials
if [ ! -f "credentials.json" ]; then
    echo "⚠️  Warning: credentials.json not found in backend directory"
    echo "Please download your Google Calendar API credentials and save as backend/credentials.json"
    echo "Visit: https://console.cloud.google.com/apis/credentials"
fi

cd ../frontend

# Setup frontend
echo "📦 Setting up frontend..."

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

cd ..

echo ""
echo "✅ Setup complete! Starting services in separate terminals..."
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "🔍 Check the terminal windows for logs:"
echo "   - Backend logs: Terminal window titled 'Friend Minder Backend'"
echo "   - Frontend logs: Terminal window titled 'Friend Minder Frontend'"
echo ""
echo "Press Ctrl+C in either terminal to stop that service"

# Start backend in new terminal
osascript <<EOF
tell application "Terminal"
    do script "cd '$(pwd)/backend' && source venv/bin/activate && echo '🔧 Starting FastAPI Backend...' && python3 main.py"
    set custom title of front window to "Friend Minder Backend"
end tell
EOF

# Wait a moment for backend to start
sleep 2

# Start frontend in new terminal
osascript <<EOF
tell application "Terminal"
    do script "cd '$(pwd)/frontend' && echo '🎨 Starting React Frontend...' && npm start"
    set custom title of front window to "Friend Minder Frontend"
end tell
EOF

echo "🎉 Both services are starting in separate terminals!"
echo "Close this terminal once both services are running."