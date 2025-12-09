#!/bin/bash

# IQE ArtNet Sniffer - Start Script
# This version sniffs ArtNet packets from the network without requiring localhost configuration

echo "Starting IQE ArtNet Sniffer..."
echo "This will monitor network traffic for ArtNet packets (port 6454)"
echo ""
echo "Features:"
echo "  - Sniffs ArtNet packets without modifying LX configuration"
echo "  - Visualizes 420x24 LED grid"
echo "  - Shows 8 ParCan flood lights with configurable radius"
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "Installing dependencies..."
    npm install
fi

# Build TypeScript
echo "Building TypeScript..."
npm run build

# Check if we need elevated privileges for packet sniffing
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Note: On macOS, packet sniffing may require:"
    echo "  1. Configuring your network switch to mirror ArtNet traffic"
    echo "  2. Using a network hub instead of a switch"
    echo "  3. Setting your network interface to promiscuous mode"
    echo ""
fi

# Start the application using the sniffer main file
echo "Starting Electron app with sniffer..."
npx electron dist/main-sniffer.js

echo "ArtNet Sniffer stopped."