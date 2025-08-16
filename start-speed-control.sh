#!/bin/bash

# Start script for the speed control webapp
# This starts both the OSC bridge and the TypeScript UI

echo "🚀 Starting IQE Speed Control System..."

# Function to kill background processes on exit
cleanup() {
    echo "🛑 Stopping services..."
    kill $(jobs -p) 2>/dev/null
    exit
}
trap cleanup EXIT INT TERM

# Start the OSC bridge (NodeJS)
echo "📡 Starting OSC WebSocket Bridge on port 8080..."
cd "$(dirname $0)/src/nodejs"
npm install --silent 2>/dev/null
IQE_WEB_PORT=8181 IQE_OSC_WS_PORT=8080 IQE_APP_OSC_TO_PORT=3232 IQE_APP_OSC_FROM_PORT=3333 node scripts.js bridge &

# Give the bridge time to start
sleep 2

# Start the TypeScript control UI
echo "🎮 Starting Speed Control UI on port 8282..."
cd "$(dirname $0)/src/control-ui"
npm install --silent 2>/dev/null
npm run start &

echo ""
echo "✅ Speed Control System Started!"
echo ""
echo "📱 Open http://localhost:8282 in your browser"
echo "   (or http://$(hostname):8282 from another device)"
echo ""
echo "⚠️  Make sure LX/Chromatik is running with OSC enabled on port 3232"
echo ""
echo "Press Ctrl+C to stop all services"

# Keep the script running
wait