#!/bin/bash
# Force ethernet to be primary network interface even with WiFi on

echo "Current network state:"
echo "===================="
ifconfig en10 | grep "inet "
ifconfig en0 | grep "status"

echo -e "\nRoutes before:"
netstat -rn | grep "^default" | head -2

# Delete any WiFi default routes
echo -e "\nRemoving WiFi routes if any..."
sudo route delete default -ifscope en0 2>/dev/null

# Ensure ethernet route exists and has lowest metric
echo "Ensuring ethernet is primary route..."
sudo route delete default 192.168.0.1 2>/dev/null
sudo route add default 192.168.0.1

echo -e "\nRoutes after:"
netstat -rn | grep "^default" | head -2

echo -e "\nTesting internet:"
ping -c 1 8.8.8.8 | head -2

echo -e "\nTo connect to PixelBlaze after this:"
echo "networksetup -setairportnetwork en0 Pixelblaze_4001A4"