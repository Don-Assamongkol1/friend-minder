#!/bin/bash

echo "🔧 Starting Friend Minder Backend..."

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

echo "🚀 Starting FastAPI server on http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
python3 main.py