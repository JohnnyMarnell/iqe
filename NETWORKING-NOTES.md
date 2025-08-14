# macOS Networking Notes & PixelBlaze Configuration Learnings

## The Great Internet Breaking Mystery - SOLVED! 🎉

### Root Cause: Internet Sharing
If you have **Internet Sharing** enabled on macOS (sharing WiFi to Ethernet for a Raspberry Pi), connecting WiFi to a different network (like PixelBlaze AP) breaks the sharing bridge and kills internet on BOTH interfaces.

**Check if Internet Sharing is enabled:**
```bash
defaults read /Library/Preferences/SystemConfiguration/com.apple.nat NAT
# Look for "Enabled = 1"
```

## Solutions for PixelBlaze Configuration with Internet Sharing

1. **Temporarily disable Internet Sharing** (easiest)
   - System Settings → General → Sharing → Internet Sharing → OFF
   - Configure your PixelBlazes
   - Turn it back ON for the Pi

2. **Use a USB WiFi adapter** (best for production)
   - Keep built-in WiFi for Internet Sharing to Pi
   - Use USB WiFi dongle for PixelBlaze connections
   - No internet disruption!

3. **Connect Pi directly to router**
   - Skip Internet Sharing entirely
   - Pi gets its own connection

## Essential macOS Network Commands

### WiFi Management
```bash
# Check WiFi power state
networksetup -getairportpower en0

# Turn WiFi on/off
networksetup -setairportpower en0 on
networksetup -setairportpower en0 off

# Get current WiFi network
networksetup -getairportnetwork en0

# Connect to a WiFi network (open network)
networksetup -setairportnetwork en0 "NetworkName"

# Connect to a WiFi network (with password)
networksetup -setairportnetwork en0 "NetworkName" "password"

# List all network services and their order
networksetup -listnetworkserviceorder

# List all hardware ports
networksetup -listallhardwareports

# Get info about a network service
networksetup -getinfo "Wi-Fi"
networksetup -getinfo "USB 10/100/1000 LAN"
```

### WiFi Scanning (Multiple Methods)

#### Method 1: Airport (Deprecated but still works)
```bash
# Basic scan
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s

# Scan with XML output
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -s -x

# Scan specific interface
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport en0 scan

# Get current WiFi info
/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I
```

**Note:** Shows warning "The airport command line tool is deprecated and will be removed in a future release"

#### Method 2: System Profiler (Slower but comprehensive)
```bash
# Get all WiFi info as text
system_profiler SPAirPortDataType

# Get as JSON (easier to parse)
system_profiler SPAirPortDataType -json

# Get as XML
system_profiler SPAirPortDataType -xml

# Quick grep for specific network
system_profiler SPAirPortDataType -json | grep -i "pixelblaze"
```

#### Method 3: wdutil (Requires sudo)
```bash
# Get WiFi info
wdutil info

# Scan for networks (requires sudo)
sudo wdutil scan

# Run diagnostics
sudo wdutil diagnose
```

### Network Interface Information
```bash
# List all interfaces with details
ifconfig

# Check specific interface
ifconfig en0    # WiFi
ifconfig en10   # USB Ethernet (number varies)

# Get just IP address
ifconfig en10 | grep "inet "

# Check interface status
ifconfig en10 | grep "status"

# Find active interfaces
ifconfig | grep "status: active"
```

### Routing Table & Internet Connectivity
```bash
# Show routing table
netstat -rn

# Show just default routes
netstat -rn | grep "^default"

# Find which interface is used for internet
route get google.com

# Test internet connectivity
ping -c 1 8.8.8.8

# Test with timeout
ping -c 1 -t 1 8.8.8.8
```

### Route Management (Requires sudo)
```bash
# Add default route
sudo route add default 192.168.0.1

# Delete default route
sudo route delete default

# Delete specific default route
sudo route delete default 192.168.0.1

# Delete WiFi-specific route
sudo route delete default -ifscope en0
```

### DHCP Management
```bash
# Renew DHCP lease (requires sudo)
sudo ipconfig set en10 DHCP

# Set manual IP
networksetup -setmanual "AX88179A" 192.168.1.3 255.255.255.0 192.168.1.1

# Switch back to DHCP
networksetup -setdhcp "AX88179A"
```

## ARP (Address Resolution Protocol)

**What is ARP?** It's the "phone book" that translates IP addresses to MAC addresses on your local network.

### How ARP Works
1. Device wants to reach an IP on same subnet
2. Broadcasts: "Who has IP x.x.x.x? Tell me your MAC!"
3. Target responds with its MAC address
4. Sender caches this MAC-to-IP mapping
5. Packets sent directly using MAC address

### ARP Commands
```bash
# Show entire ARP table
arp -a

# Show ARP entries for specific subnet
arp -a | grep "10.10.42"

# Delete ARP entry (forces re-discovery)
sudo arp -d 10.10.42.68

# Watch ARP in action
sudo arp -d 10.10.42.68  # Clear entry
ping -c 1 10.10.42.68     # Triggers ARP request
arp -a | grep "10.10.42"  # See new entry!
```

### Key ARP Facts
- Only works on **same subnet** (can't ARP across routers)
- Entries expire after ~20 minutes
- No gateway needed for same-subnet communication
- `169.254.x.x` addresses also use ARP (link-local)

## Setting Up Manual IP for Direct Device Connection

When connecting directly to devices like ArtNet controllers:

```bash
# Find your ethernet adapter name
networksetup -listallhardwareports | grep -A2 "Ethernet"

# Set manual IP (permanent)
sudo networksetup -setmanual "USB 10/100/1000 LAN" 10.10.42.11 255.255.255.0 10.10.42.1

# Or temporary IP
sudo ifconfig en8 inet 10.10.42.11 netmask 255.255.255.0

# Verify it worked
ifconfig en8 | grep "inet "
ping 10.10.42.68

# Check ARP discovered the device
arp -a | grep "10.10.42"
```

## The Fucking Network Priority Problem

**CRITICAL:** macOS uses network service order to determine internet routing. If a non-internet ethernet adapter is higher priority than WiFi, internet breaks!

### Check Service Order
```bash
networksetup -listnetworkserviceorder
```

### Fix Service Order (WiFi first for internet)
```bash
sudo networksetup -ordernetworkservices "Wi-Fi" "USB 10/100/1000 LAN" "Other Services..."
```

### Why Ethernet Adapters Break Internet
1. Plug in ethernet adapter
2. macOS puts it high in priority (often #2)
3. Tries to route internet through it
4. But it has no real gateway/internet
5. **Internet dead** 🪦

### Solutions:
- **Reorder services** with WiFi first
- **Unplug ethernet** when not needed
- **Disable the service** in Network settings
- **Use different subnets** so routing is clear

### Advanced Diagnostics

#### Check macOS Network Reachability
```bash
# What interfaces does macOS think can reach internet?
scutil --nwi

# Can macOS reach a specific host?
scutil -r google.com

# Which interface would be used for internet?
route get 8.8.8.8 | grep interface
```

#### Interface Status Commands
```bash
# Check if cable is connected (link status)
ifconfig en8 | grep "status"
# active = cable connected
# inactive = no cable

# See all UP interfaces
ifconfig | grep -E "^[a-z].*: flags=.*<UP"

# Check interface metrics/priority
route -n get default -ifscope en0
```

#### Quick Fixes When Internet Breaks
```bash
# Option 1: Delete bad default route
sudo route delete default -ifscope en8

# Option 2: Force route through WiFi
sudo route add default 192.168.0.1 -ifscope en0

# Option 3: Temporarily disable IPv4 on ethernet
sudo networksetup -setv4off "USB 10/100/1000 LAN"

# Option 4: Create location without ethernet
networksetup -createlocation "Internet Only" populate
networksetup -switchtolocation "Internet Only"
```

### Network Diagnostic Script

Run `src/pixelblaze/network_diagnostic.sh` when ethernet breaks internet:
```bash
./src/pixelblaze/network_diagnostic.sh > network_broken.txt
```

This captures:
- Service order
- Active interfaces
- Default routes
- Reachability status
- Which interface is being used
- Ping/DNS tests
- Quick fix commands

### Why macOS Is Dumb About This

**What SHOULD happen:**
- Check reachability before routing
- Skip interfaces without gateways for internet
- Use metrics/weights like Linux
- Detect "local only" networks

**What ACTUALLY happens:**
- Blindly follows service order
- Sees active link + IP = "must be internet!"
- Doesn't test actual connectivity
- Routes everything to dead end

**Linux does it better:** NetworkManager uses connection profiles and dynamic metrics
**Windows does it better:** Automatic metric assignment based on link speed/type
**macOS:** "lol get fucked, unplug your cable"

### The Mystery of Multiple Default Routes

macOS can have MULTIPLE default routes simultaneously:
```bash
# See all default routes
netstat -rn | grep "^default"

# Example of problematic state:
default 192.168.0.1        en0     # Real internet (WiFi)
default 10.10.42.1         en8     # Fake gateway (ethernet to ArtNet)
default link#26            utun6   # VPN tunnel
```

**The Time Bomb:** Even with correct service order, macOS may ADD a default route for ethernet after connecting. This route might randomly become primary, killing internet.

#### Check which route is actually being used:
```bash
# Which interface for internet?
route get 8.8.8.8 | grep interface

# Delete bogus default routes
sudo route delete default 10.10.42.1
```

#### Why Internet Randomly Dies Later:
1. **Initially:** WiFi route has priority, everything works
2. **macOS adds:** Default route through ethernet (even though it goes nowhere)
3. **Something triggers:** Route table recalculation (sleep/wake, network change, phase of moon)
4. **macOS decides:** "Let's try ethernet first now!"
5. **Result:** Internet dead, you're fucked

#### Prevention (sort of):
```bash
# Delete the bad route when you see it
sudo route delete default 10.10.42.1

# Or remove all default routes for specific interface
sudo route delete default -ifscope en8

# Nuclear option: Flush all routes and rebuild
sudo route -n flush
# (WiFi will rebuild its routes automatically)
```

#### Monitoring for the Time Bomb:
```bash
# Watch routes in real-time
while true; do 
    clear
    echo "=== $(date +%H:%M:%S) ==="
    netstat -rn | grep "^default"
    echo ""
    echo "Internet via: $(route get 8.8.8.8 | grep interface | awk '{print $2}')"
    sleep 5
done
```

## Common Issues & Solutions

### Issue: Ethernet has no IP address
```bash
# Check if interface is up
ifconfig en10 | grep "status"

# If manual IP configured but not working
networksetup -getinfo "AX88179A"  # Check settings
networksetup -setdhcp "AX88179A"   # Switch to DHCP

# Force DHCP renewal
sudo ipconfig set en10 DHCP
```

### Issue: Multiple default routes causing confusion
```bash
# See all default routes
netstat -rn | grep "^default"

# You might see:
# - IPv4 routes (192.168.x.x)
# - IPv6 routes (fe80::)
# - VPN routes (utun interfaces)
# - Link-local routes

# Fix by ensuring correct priority
sudo route delete default
sudo route add default 192.168.0.1  # Your router IP
```

### Issue: Can't find network interface name
```bash
# Find ethernet adapters
networksetup -listallhardwareports | grep -A2 "Ethernet"

# Find which en* number is assigned
ifconfig | grep -B3 "status: active"
```

## PixelBlaze Specific Notes

### PixelBlaze AP Mode
- SSID Format: `Pixelblaze_XXXXXX` (where XXXXXX is device ID)
- Default IP: `192.168.4.1`
- Security: Open (no password)
- To enter AP mode: Hold button while powering on until LED flashes

### Scanning for PixelBlaze
```bash
# Quick scan with grep
system_profiler SPAirPortDataType -json | grep -i pixel

# With jq for better parsing (if installed)
system_profiler SPAirPortDataType -json | jq '.SPAirPortDataType[].spairport_airport_interfaces[].spairport_airport_other_local_wireless_networks[]._name' | grep -i pixel
```

## Network Service Priority

macOS uses service order to determine which interface to use:

```bash
# View current order
networksetup -listnetworkserviceorder

# Change order (example)
networksetup -ordernetworkservices "Ethernet" "Wi-Fi" "iPhone USB"
```

**Important:** Higher priority services are used first for internet routing.

## Python/programmatic WiFi Detection

### Using pyobjc (built into macOS Python)
```python
import objc
objc.loadBundle('CoreWLAN', globals(),
                bundle_path='/System/Library/Frameworks/CoreWLAN.framework')

interface = CWInterface.interface()
networks, error = interface.scanForNetworksWithSSID_error_(None, None)
```

### Parsing system_profiler JSON
```python
import subprocess
import json

result = subprocess.run(['system_profiler', 'SPAirPortDataType', '-json'],
                       capture_output=True, text=True)
data = json.loads(result.stdout)
```

## Key Learnings

1. **Internet Sharing is complex** - It creates a bridge that breaks when WiFi changes networks
2. **Route tables matter** - macOS can have multiple default routes causing confusion
3. **DHCP vs Manual IP** - Manual IP config can fail silently; DHCP is more reliable
4. **WiFi must be ON to scan** - Even system_profiler needs WiFi enabled
5. **Ethernet adapters vary** - Could be en8, en10, etc. - always detect dynamically
6. **airport is deprecated** - But still works; system_profiler is the modern replacement
7. **Column parsing is tricky** - netstat output has variable column positions

## Desert Survival Tips 🏜️

1. **Pre-configure everything possible** - Don't rely on internet
2. **Use static IPs if router is flaky** - But document them!
3. **Have backup WiFi dongles** - USB WiFi adapters are lifesavers
4. **Test ALL scenarios before leaving** - Including power cycling everything
5. **Print this document** - Paper doesn't need internet
6. **Consider a portable router** - Create your own reliable network
7. **Label everything** - Device IDs, IPs, purposes

## Quick Debug Checklist

When internet stops working:
1. ✓ Check Internet Sharing status
2. ✓ Check which interface has default route: `netstat -rn | grep "^default"`
3. ✓ Verify ethernet has IP: `ifconfig en10 | grep "inet "`
4. ✓ Test connectivity: `ping -c 1 8.8.8.8`
5. ✓ Check WiFi status: `networksetup -getairportnetwork en0`
6. ✓ Reset if needed: Unplug/replug ethernet, toggle WiFi

## The Nuclear Option

When all else fails:
```bash
# Reset all network settings
sudo dscacheutil -flushcache
sudo killall -HUP mDNSResponder

# Or just reboot
sudo reboot
```

---

*Generated from our debugging session where we discovered Internet Sharing was the root cause of all the network problems. May this document save future souls from network hell.* 🙏