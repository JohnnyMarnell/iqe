#!/bin/bash

echo "Starting IQE ArtNet Electron app with console output..."
echo "Look for console messages in the terminal..."
echo ""

# Run electron with console output visible
npm run build && npx electron . --enable-logging