#!/bin/bash
# Network Diagnostic Script
# Run this when ethernet adapter is breaking internet
# Save output to share when reconnected

echo "==================================="
echo "NETWORK DIAGNOSTIC REPORT"
echo "Time: $(date)"
echo "==================================="

echo -e "\n### 1. NETWORK SERVICE ORDER ###"
networksetup -listnetworkserviceorder | head -20

echo -e "\n### 2. ACTIVE INTERFACES ###"
ifconfig | grep -E "^[a-z].*: flags=.*<UP" | cut -d: -f1 | while read iface; do
    echo -e "\n$iface:"
    ifconfig $iface | grep -E "status:|inet " | sed 's/^/  /'
done

echo -e "\n### 3. DEFAULT ROUTES ###"
netstat -rn | grep "^default" | head -10

echo -e "\n### 4. WHICH INTERFACE FOR INTERNET? ###"
echo "Route to 8.8.8.8 (Google DNS):"
route get 8.8.8.8 2>&1 | grep -E "interface:|gateway:" | sed 's/^/  /'

echo -e "\n### 5. REACHABILITY STATUS ###"
echo "macOS Network Reachability:"
scutil --nwi

echo -e "\n### 6. CAN WE REACH INTERNET? ###"
echo "Testing google.com reachability:"
scutil -r google.com

echo -e "\n### 7. ACTUAL PING TEST ###"
echo "Ping 8.8.8.8 (3 attempts):"
ping -c 3 -t 2 8.8.8.8 2>&1 | grep -E "bytes from|0 packets received|timeout" | head -3

echo -e "\n### 8. DNS RESOLUTION TEST ###"
echo "Can we resolve google.com?"
nslookup google.com 2>&1 | grep -E "Server:|Address:|Non-authoritative|can't" | head -5

echo -e "\n### 9. INTERFACE METRICS/PRIORITIES ###"
echo "Interface priorities (lower = preferred):"
for iface in en0 en8 en10; do
    if ifconfig $iface >/dev/null 2>&1; then
        metric=$(route -n get default -ifscope $iface 2>/dev/null | grep "ifscope" | awk '{print $2}')
        echo "  $iface: ${metric:-not set}"
    fi
done

echo -e "\n### 10. ARP TABLE (LOCAL DEVICES) ###"
arp -a | grep -E "10.10.42|192.168" | head -10

echo -e "\n### 11. INTERNET SHARING STATUS ###"
echo "Internet Sharing enabled?"
defaults read /Library/Preferences/SystemConfiguration/com.apple.nat NAT 2>/dev/null | grep "Enabled = " | head -1

echo -e "\n### 12. QUICK FIX COMMANDS TO TRY ###"
echo "# Option 1: Reorder services (puts WiFi first):"
echo "sudo networksetup -ordernetworkservices \"Wi-Fi\" \"USB 10/100/1000 LAN\" \"AX88179A\""
echo ""
echo "# Option 2: Delete bad default route:"
echo "sudo route delete default -ifscope en8"
echo ""
echo "# Option 3: Force default through WiFi:"
echo "sudo route add default 192.168.0.1 -ifscope en0"
echo ""
echo "# Option 4: Disable IPv4 on ethernet:"
echo "sudo networksetup -setv4off \"USB 10/100/1000 LAN\""
echo "(Re-enable with: sudo networksetup -setmanual \"USB 10/100/1000 LAN\" 10.10.42.11 255.255.255.0)"

echo -e "\n==================================="
echo "END DIAGNOSTIC REPORT"
echo "==================================="