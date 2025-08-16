#!/bin/bash

# Simple startup script for the unified speed control system

cd "$(dirname $0)/src/control-ui"

echo "🚀 Starting Speed Control System..."
echo ""

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
fi

# Build the frontend if needed
if [ ! -d "dist" ]; then
    echo "🔨 Building frontend..."
    npm run build
fi

# Start the unified server
echo "✨ Starting unified server (OSC bridge + Web UI)..."
echo ""
npm start