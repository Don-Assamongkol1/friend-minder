#!/bin/bash

echo "🎨 Starting Friend Minder Frontend..."

cd frontend

# Install frontend dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

echo "🚀 Starting React development server on http://localhost:3000"
echo ""
npm start