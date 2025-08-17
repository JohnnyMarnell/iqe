#!/bin/bash
# Install script for PixelBlaze Monitor on Raspberry Pi Zero

echo "Installing PixelBlaze Monitor service..."

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --no-cache-dir fastapi uvicorn websockets requests

# Copy service file
echo "Installing systemd service..."
sudo cp pixelblaze-monitor.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable pixelblaze-monitor.service

# Start the service
sudo systemctl start pixelblaze-monitor.service

echo "Installation complete!"
echo ""
echo "Commands:"
echo "  Check status:  sudo systemctl status pixelblaze-monitor"
echo "  View logs:     sudo journalctl -u pixelblaze-monitor -f"
echo "  Restart:       sudo systemctl restart pixelblaze-monitor"
echo "  Stop:          sudo systemctl stop pixelblaze-monitor"
echo ""
echo "Access the monitor at: http://$(hostname -I | cut -d' ' -f1):8000"