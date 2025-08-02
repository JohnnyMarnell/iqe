#!/bin/bash

echo "IQE ArtNet LED Visualizer - Electron Version"
echo "==========================================="
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build TypeScript
echo "Building TypeScript..."
npm run build

# Start Electron
echo "Starting Electron app..."
npm start