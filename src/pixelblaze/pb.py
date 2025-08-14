#!/usr/bin/env python3
"""
PixelBlaze Fleet Management CLI
Unified tool for managing PixelBlaze devices
"""

import click
import subprocess
import json
import time
import sys
import os
import re
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

# Configuration
DEFAULT_INTERFACE = "en0"
AP_IP = "192.168.4.1"
CONFIG_DIR = Path("./pixelblaze")
FLEET_CONFIG = CONFIG_DIR / "fleet.json"
LOGS_DIR = CONFIG_DIR / "logs"

# Ensure config directories exist
CONFIG_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)


class PixelBlazeManager:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.interface = DEFAULT_INTERFACE
        self.log_file = LOGS_DIR / f"pb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
    def log(self, message: str, error: bool = False):
        """Log to console and file"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        if error:
            click.secho(log_entry, fg='red', err=True)
        elif self.verbose or error:
            click.echo(log_entry)
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + "\n")
    
    def scan_networks(self) -> List[Dict]:
        """Scan for WiFi networks using system_profiler"""
        # Ensure WiFi is on first
        wifi_check = subprocess.run(
            ['networksetup', '-getairportpower', self.interface],
            capture_output=True,
            text=True
        )
        
        if 'Off' in wifi_check.stdout:
            # Turn WiFi on
            subprocess.run(
                ['networksetup', '-setairportpower', self.interface, 'on'],
                capture_output=True
            )
            time.sleep(2)  # Give it time to start
        
        try:
            result = subprocess.run(
                ['system_profiler', 'SPAirPortDataType', '-json'],
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode != 0:
                return []
            
            data = json.loads(result.stdout)
            networks = []
            
            if 'SPAirPortDataType' in data:
                for item in data['SPAirPortDataType']:
                    if 'spairport_airport_interfaces' in item:
                        for interface in item['spairport_airport_interfaces']:
                            if 'spairport_airport_other_local_wireless_networks' in interface:
                                for network in interface['spairport_airport_other_local_wireless_networks']:
                                    ssid = network.get('_name', '')
                                    if ssid:
                                        networks.append({
                                            'ssid': ssid,
                                            'channel': network.get('spairport_network_channel', ''),
                                            'bssid': network.get('spairport_network_bssid', ''),
                                            'rssi': network.get('spairport_signal_rssi', ''),
                                        })
            
            return networks
        except Exception as e:
            self.log(f"Scan error: {e}", error=True)
            return []
    
    def find_pixelblaze_networks(self, networks: List[Dict]) -> List[Dict]:
        """Filter networks to find PixelBlaze devices"""
        pattern = re.compile(r'pixelblaze', re.IGNORECASE)
        return [n for n in networks if pattern.search(n['ssid'])]
    
    def connect_to_network(self, ssid: str) -> bool:
        """Connect to a WiFi network"""
        result = subprocess.run(
            ['networksetup', '-setairportnetwork', self.interface, ssid],
            capture_output=True,
            text=True
        )
        
        if "Could not find" in result.stderr:
            return False
        
        time.sleep(3)
        
        # Verify connection
        result = subprocess.run(
            ['networksetup', '-getairportnetwork', self.interface],
            capture_output=True,
            text=True
        )
        
        return ssid in result.stdout
    
    def get_current_network(self) -> Optional[str]:
        """Get current WiFi network"""
        result = subprocess.run(
            ['networksetup', '-getairportnetwork', self.interface],
            capture_output=True,
            text=True
        )
        
        if "Current Wi-Fi Network:" in result.stdout:
            return result.stdout.split("Current Wi-Fi Network:")[1].strip()
        return None
    
    def save_fleet_config(self, devices: List[Dict]):
        """Save fleet configuration"""
        config = {
            "last_scan": datetime.now().isoformat(),
            "devices": devices
        }
        
        # Load existing config if it exists
        if FLEET_CONFIG.exists():
            with open(FLEET_CONFIG, 'r') as f:
                existing = json.load(f)
                # Merge devices
                existing_ids = {d['device_id'] for d in existing.get('devices', [])}
                for device in devices:
                    if device['device_id'] not in existing_ids:
                        existing.setdefault('devices', []).append(device)
                config = existing
                config['last_scan'] = datetime.now().isoformat()
        
        with open(FLEET_CONFIG, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_fleet_config(self) -> Dict:
        """Load fleet configuration"""
        if not FLEET_CONFIG.exists():
            return {}
        
        with open(FLEET_CONFIG, 'r') as f:
            return json.load(f)


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Verbose output')
@click.pass_context
def cli(ctx, verbose):
    """PixelBlaze Fleet Management Tool
    
    Manage multiple PixelBlaze LED controllers from the command line.
    """
    ctx.obj = PixelBlazeManager(verbose=verbose)


@cli.command()
@click.option('--continuous', '-c', is_flag=True, help='Continuous scanning')
@click.option('--interval', '-i', default=10, help='Scan interval in seconds')
@click.pass_obj
def scan(manager, continuous, interval):
    """Scan for PixelBlaze devices in AP mode"""
    click.secho("Scanning for PixelBlaze devices...", fg='cyan')
    
    found_devices = {}
    
    def do_scan():
        networks = manager.scan_networks()
        pixelblaze_networks = manager.find_pixelblaze_networks(networks)
        
        if not pixelblaze_networks:
            click.echo("No PixelBlaze devices found in AP mode")
            if not continuous:
                click.echo("\nTo put PixelBlaze in AP mode:")
                click.echo("1. Hold button while powering on")
                click.echo("2. Wait for LED to flash")
                click.echo("3. Release button")
            return pixelblaze_networks
        
        click.secho(f"\nFound {len(pixelblaze_networks)} PixelBlaze device(s):", fg='green')
        for pb in pixelblaze_networks:
            device_id = pb['ssid'].split('_')[-1] if '_' in pb['ssid'] else pb['ssid']
            
            if pb['ssid'] not in found_devices:
                click.secho(f"  🆕 {pb['ssid']} (ID: {device_id})", fg='yellow')
                found_devices[pb['ssid']] = {
                    'ssid': pb['ssid'],
                    'device_id': device_id,
                    'channel': pb.get('channel', ''),
                    'first_seen': datetime.now().isoformat()
                }
            else:
                click.echo(f"  • {pb['ssid']} (ID: {device_id})")
            
            if pb.get('rssi'):
                click.echo(f"    Signal: {pb['rssi']} dBm")
            if pb.get('channel'):
                click.echo(f"    Channel: {pb['channel']}")
        
        return pixelblaze_networks
    
    if continuous:
        click.echo(f"Continuous scanning every {interval} seconds (Ctrl+C to stop)\n")
        try:
            while True:
                do_scan()
                time.sleep(interval)
        except KeyboardInterrupt:
            click.echo("\n\nScan stopped")
            if found_devices:
                # Save found devices
                manager.save_fleet_config(list(found_devices.values()))
                click.secho(f"\nSaved {len(found_devices)} device(s) to fleet config", fg='green')
    else:
        pixelblaze = do_scan()
        if pixelblaze:
            devices = []
            for pb in pixelblaze:
                device_id = pb['ssid'].split('_')[-1] if '_' in pb['ssid'] else pb['ssid']
                devices.append({
                    'ssid': pb['ssid'],
                    'device_id': device_id,
                    'channel': pb.get('channel', ''),
                    'discovered': datetime.now().isoformat()
                })
            manager.save_fleet_config(devices)
            click.secho(f"\nSaved {len(devices)} device(s) to fleet config", fg='green')


@cli.command()
@click.argument('device_id', required=False)
@click.pass_obj
def connect(manager, device_id):
    """Connect to a PixelBlaze device (requires sudo for network routing)"""
    # Check if running with sudo
    if os.geteuid() != 0:
        click.secho("This command requires sudo to fix network routing", fg='red')
        click.echo("Run: sudo python pb.py connect")
        return
    
    # Check for Internet Sharing - this breaks everything!
    sharing_check = subprocess.run(
        ['defaults', 'read', '/Library/Preferences/SystemConfiguration/com.apple.nat', 'NAT'],
        capture_output=True,
        text=True
    )
    
    if 'Enabled = 1' in sharing_check.stdout:
        click.secho("⚠️  WARNING: Internet Sharing is ON!", fg='yellow', bold=True)
        click.echo("This is why your internet breaks when connecting to PixelBlaze!")
        click.echo("\nInternet Sharing bridges WiFi → Ethernet for your Pi.")
        click.echo("Connecting WiFi to PixelBlaze breaks this bridge.\n")
        click.echo("Solutions:")
        click.echo("1. Temporarily turn off Internet Sharing in System Settings")
        click.echo("2. Use a USB WiFi adapter for PixelBlaze connections")
        click.echo("3. Connect Pi directly to router instead of through Mac")
        
        if not click.confirm("\nContinue anyway? (Internet WILL break)"):
            click.echo("\nTo disable Internet Sharing:")
            click.echo("System Settings → General → Sharing → Internet Sharing → OFF")
            return
    
    # Ensure WiFi is on
    click.echo("Checking WiFi status...")
    wifi_status = subprocess.run(
        ['networksetup', '-getairportpower', manager.interface],
        capture_output=True,
        text=True
    )
    
    if 'Off' in wifi_status.stdout:
        click.echo("WiFi is off, turning it on...")
        subprocess.run(
            ['networksetup', '-setairportpower', manager.interface, 'on'],
            capture_output=True
        )
        time.sleep(3)  # Give WiFi more time to fully start
    else:
        click.echo("WiFi is already on")
    
    # Scan for PixelBlaze devices - retry a few times as WiFi initializes
    click.echo("Scanning for PixelBlaze devices in AP mode...")
    pixelblaze_networks = []
    for attempt in range(3):
        networks = manager.scan_networks()
        pixelblaze_networks = manager.find_pixelblaze_networks(networks)
        
        if pixelblaze_networks:
            break
        
        if attempt < 2:
            click.echo(f"  No devices found, retrying... ({attempt + 2}/3)")
            time.sleep(3)
    
    if pixelblaze_networks:
        click.secho(f"Found {len(pixelblaze_networks)} PixelBlaze device(s) broadcasting:", fg='green')
        for pb in pixelblaze_networks:
            pb_id = pb['ssid'].split('_')[-1] if '_' in pb['ssid'] else pb['ssid']
            click.echo(f"  • {pb['ssid']} (ID: {pb_id}, Channel: {pb.get('channel', 'unknown')})")
    else:
        click.secho("No PixelBlaze devices found in AP mode", fg='yellow')
        click.echo("Make sure device is powered on with button held until LED flashes")
        return
    
    # Load config for saving updates
    config = manager.load_fleet_config()
    devices = config.get('devices', [])
    
    # Find device to connect to
    device = None
    
    if device_id:
        # User specified a device ID - look for it in current scan
        for pb in pixelblaze_networks:
            pb_id = pb['ssid'].split('_')[-1] if '_' in pb['ssid'] else pb['ssid']
            if pb_id == device_id:
                device = pb
                device['device_id'] = pb_id
                break
        
        if not device:
            click.secho(f"Device {device_id} not found in current scan", fg='red')
            click.echo("Available devices:")
            for pb in pixelblaze_networks:
                pb_id = pb['ssid'].split('_')[-1] if '_' in pb['ssid'] else pb['ssid']
                click.echo(f"  • ID: {pb_id}")
            return
    else:
        # No device specified - use first one found
        if pixelblaze_networks:
            device = pixelblaze_networks[0]
            device['device_id'] = device['ssid'].split('_')[-1] if '_' in device['ssid'] else device['ssid']
            click.secho(f"\nAuto-selecting first found: {device['ssid']}", fg='cyan')
        else:
            click.secho("No devices to connect to", fg='red')
            return
    
    # Update config with this device if new
    existing = next((d for d in devices if d['device_id'] == device['device_id']), None)
    if not existing:
        devices.append({
            'ssid': device['ssid'],
            'device_id': device['device_id'],
            'channel': device.get('channel', ''),
            'discovered': datetime.now().isoformat()
        })
        config['devices'] = devices
        with open(FLEET_CONFIG, 'w') as f:
            json.dump(config, f, indent=2)
    
    # Store current network
    current = manager.get_current_network()
    if current:
        click.echo(f"Current network: {current}")
    
    # Find active ethernet interface with internet
    click.echo("\nFinding active ethernet interface...")
    ethernet_gateway = None
    ethernet_interface = None
    
    result = subprocess.run(
        ['netstat', '-rn'],
        capture_output=True,
        text=True
    )
    
    for line in result.stdout.split('\n'):
        if line.startswith('default'):
            parts = line.split()
            if len(parts) >= 4:
                gateway = parts[1]
                # Interface might be in different positions depending on flags
                interface = None
                for part in parts[3:]:
                    if part.startswith('en') or part.startswith('bridge'):
                        interface = part
                        break
                
                if not interface:
                    continue
                    
                # Check if it's an ethernet interface (not WiFi, not VPN)
                if interface not in ['en0', 'lo0'] and not interface.startswith('utun'):
                    # Skip IPv6 gateways for now
                    if '::' in gateway or 'fe80' in gateway or 'link' in gateway:
                        continue
                        
                    # Verify it has an IP
                    check = subprocess.run(
                        ['ifconfig', interface],
                        capture_output=True,
                        text=True
                    )
                    if 'inet ' in check.stdout and 'status: active' in check.stdout:
                        ethernet_gateway = gateway
                        ethernet_interface = interface
                        click.secho(f"✓ Found ethernet: {interface} with gateway {gateway}", fg='green')
                        break
    
    if not ethernet_gateway:
        click.secho("⚠️  No active ethernet with internet found", fg='yellow')
        click.echo("Make sure ethernet is connected and has internet before running this")
        if not click.confirm("Try to continue anyway?"):
            return
    
    # Connect
    click.echo(f"Connecting to {device['ssid']}...")
    if manager.connect_to_network(device['ssid']):
        click.secho(f"✅ Connected to {device['ssid']}", fg='green')
        
        # Fix network routing to maintain internet through ethernet
        if ethernet_gateway:
            click.echo(f"\nFixing network routing to maintain internet via {ethernet_interface}...")
            
            # Step 1: Set network service order to prioritize ethernet
            click.echo("  Setting network service order (ethernet first)...")
            # Get list of network services
            services_out = subprocess.run(
                ['networksetup', '-listnetworkserviceorder'],
                capture_output=True,
                text=True
            ).stdout
            
            # Find ethernet service name (might be "USB 10/100/1000 LAN" or "AX88179A" etc)
            ethernet_service = None
            for line in services_out.split('\n'):
                if ethernet_interface in line:
                    # Previous line has the service name
                    idx = services_out.split('\n').index(line)
                    if idx > 0:
                        service_line = services_out.split('\n')[idx - 1]
                        if ')' in service_line:
                            ethernet_service = service_line.split(')', 1)[1].strip()
                            break
            
            if ethernet_service:
                # Set ethernet as highest priority
                subprocess.run(
                    ['networksetup', '-ordernetworkservices', ethernet_service, 'Wi-Fi'],
                    capture_output=True
                )
                click.echo(f"  Set {ethernet_service} as primary network")
            
            # Step 2: Remove any default routes created by WiFi
            click.echo("  Removing WiFi default routes...")
            subprocess.run(
                ['sudo', 'route', 'delete', 'default', '-interface', 'en0'],
                capture_output=True
            )
            
            # Step 3: Ensure ethernet has the default route
            click.echo(f"  Ensuring default route via ethernet ({ethernet_gateway})...")
            subprocess.run(
                ['sudo', 'route', 'delete', 'default'],
                capture_output=True
            )
            subprocess.run(
                ['sudo', 'route', 'add', 'default', ethernet_gateway],
                capture_output=True
            )
            
            # Step 4: Add specific route for PixelBlaze subnet ONLY
            click.echo("  Adding route for PixelBlaze (192.168.4.0/24) via WiFi...")
            subprocess.run(
                ['sudo', 'route', 'add', '-net', '192.168.4.0/24', '-interface', 'en0'],
                capture_output=True
            )
            
            # Test both connections
            click.echo("\nTesting connections:")
            
            # Test internet via ethernet
            internet_test = subprocess.run(
                ['ping', '-c', '1', '-t', '1', '8.8.8.8'],
                capture_output=True
            )
            
            if internet_test.returncode == 0:
                click.secho("  ✅ Internet working via ethernet", fg='green')
            else:
                click.secho("  ❌ Internet test failed", fg='red')
                click.echo("  Try: sudo route add default " + ethernet_gateway)
            
            # Test PixelBlaze access
            pb_test = subprocess.run(
                ['ping', '-c', '1', '-t', '1', '192.168.4.1'],
                capture_output=True
            )
            
            if pb_test.returncode == 0:
                click.secho("  ✅ PixelBlaze accessible via WiFi", fg='green')
            else:
                click.echo("  ⚠️  Can't ping PixelBlaze yet (may still be connecting)")
        
        click.echo(f"\nPixelBlaze config page: http://{AP_IP}")
        
        if click.confirm("Open in browser?"):
            subprocess.run(['open', f'http://{AP_IP}'])
        
        click.echo("\nPress Enter when done to restore previous network...")
        input()
        
        if current:
            click.echo(f"Restoring connection to {current}...")
            subprocess.run(
                ['networksetup', '-setairportnetwork', manager.interface, current],
                capture_output=True
            )
    else:
        click.secho(f"Failed to connect to {device['ssid']}", fg='red')
        click.echo("Make sure device is in AP mode")


@cli.command()
@click.option('--ssid', prompt='Target WiFi SSID', help='WiFi network name')
@click.option('--password', prompt='WiFi password', hide_input=True, help='WiFi password')
@click.option('--all', 'flash_all', is_flag=True, help='Flash all devices')
@click.pass_obj
def flash(manager, ssid, password, flash_all):
    """Configure PixelBlaze devices to join WiFi network"""
    config = manager.load_fleet_config()
    devices = config.get('devices', [])
    
    if not devices:
        click.secho("No devices in fleet config. Run 'pb scan' first.", fg='red')
        return
    
    # Filter devices to flash
    if not flash_all:
        click.echo("Select devices to configure:")
        selected = []
        for d in devices:
            if click.confirm(f"  Configure {d['ssid']}?"):
                selected.append(d)
        devices = selected
    
    if not devices:
        click.echo("No devices selected")
        return
    
    click.secho(f"\nWill configure {len(devices)} device(s) to join: {ssid}", fg='cyan')
    
    # Store current network
    original = manager.get_current_network()
    
    # Process each device
    for i, device in enumerate(devices, 1):
        click.echo(f"\n[{i}/{len(devices)}] Processing {device['ssid']}...")
        
        if manager.connect_to_network(device['ssid']):
            click.secho(f"  ✅ Connected", fg='green')
            
            # Open browser
            click.echo("  Opening configuration page...")
            subprocess.run(['open', f'http://{AP_IP}'])
            
            click.echo("\n" + "="*40)
            click.echo("CONFIGURE IN BROWSER:")
            click.echo(f"1. Set WiFi SSID: {ssid}")
            click.echo(f"2. Set WiFi Password: {'*' * len(password)}")
            click.echo("3. Save configuration")
            click.echo("="*40)
            
            click.prompt("\nPress Enter when configured")
            
            # Update device status
            device['configured'] = True
            device['target_network'] = ssid
            device['configured_time'] = datetime.now().isoformat()
        else:
            click.secho(f"  ❌ Could not connect", fg='red')
    
    # Save updated config
    with open(FLEET_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)
    
    # Restore original network
    if original:
        click.echo(f"\nRestoring connection to {original}...")
        subprocess.run(
            ['networksetup', '-setairportnetwork', manager.interface, original],
            capture_output=True
        )
    
    # Summary
    configured = sum(1 for d in devices if d.get('configured'))
    click.secho(f"\n✅ Configured {configured}/{len(devices)} devices", fg='green')


@cli.command()
@click.pass_obj
def list(manager):
    """List known PixelBlaze devices"""
    config = manager.load_fleet_config()
    devices = config.get('devices', [])
    
    if not devices:
        click.echo("No devices in fleet config")
        return
    
    click.secho(f"\nKnown PixelBlaze devices ({len(devices)}):", fg='cyan')
    
    for device in devices:
        status = "✅" if device.get('configured') else "⚪"
        
        # Show name/label in header if present
        display_name = device['ssid']
        if device.get('name'):
            display_name = f"{device['name']} ({device['ssid']})"
        
        click.echo(f"\n{status} {display_name}")
        click.echo(f"   ID: {device['device_id']}")
        
        if device.get('label') is not None:
            click.echo(f"   Label: {device['label']}")
        
        if device.get('channel'):
            click.echo(f"   Channel: {device['channel']}")
        
        if device.get('configured'):
            click.echo(f"   Network: {device.get('target_network', 'unknown')}")
            click.echo(f"   Configured: {device.get('configured_time', 'unknown')}")
        
        if device.get('discovered'):
            click.echo(f"   Discovered: {device['discovered']}")


@cli.command()
@click.option('--device-id', '-d', help='Device ID to label')
@click.option('--label', '-l', type=int, help='Numeric label for the device')
@click.option('--name', '-n', help='Custom name for the device')
@click.pass_obj
def label(manager, device_id, label, name):
    """Label/name a PixelBlaze device for identification
    
    With no arguments: Continuously scan and prompt for unlabeled devices
    """
    # If no arguments, run continuous labeling mode
    if not label and not name and not device_id:
        click.secho("Continuous labeling mode - scanning for devices", fg='cyan')
        click.echo("Press Ctrl+C to stop\n")
        
        seen_devices = set()  # Track what we've seen
        scan_count = 0
        
        try:
            while True:
                scan_count += 1
                timestamp = time.strftime('%H:%M:%S')
                
                # Scan for devices
                click.echo(f"[{timestamp}] Scanning... (#{scan_count})", nl=False)
                networks = manager.scan_networks()
                pixelblaze_networks = manager.find_pixelblaze_networks(networks)
                click.echo(f" - found {len(pixelblaze_networks)} PixelBlaze(s)")
                
                # Load current config each time
                config = manager.load_fleet_config()
                existing_devices = {d['device_id']: d for d in config.get('devices', [])}
                
                current_scan_ids = set()
                
                for pb in pixelblaze_networks:
                    device_id = pb['ssid'].split('_')[-1] if '_' in pb['ssid'] else pb['ssid']
                    current_scan_ids.add(device_id)
                    
                    # Log if newly appeared
                    if device_id not in seen_devices:
                        click.secho(f"  📡 Appeared: {pb['ssid']} (ID: {device_id})", fg='green')
                        seen_devices.add(device_id)
                        
                        # Save to config if new
                        if device_id not in existing_devices:
                            device = {
                                'ssid': pb['ssid'],
                                'device_id': device_id,
                                'channel': pb.get('channel', ''),
                                'discovered': datetime.now().isoformat()
                            }
                            config.setdefault('devices', []).append(device)
                            existing_devices[device_id] = device
                            
                            # Save config
                            config['last_scan'] = datetime.now().isoformat()
                            with open(FLEET_CONFIG, 'w') as f:
                                json.dump(config, f, indent=2)
                    
                    # Check if needs labeling or naming
                    if device_id in existing_devices:
                        device = existing_devices[device_id]
                        needs_update = False
                        
                        if device.get('label') is None:
                            # Found unlabeled device
                            click.secho(f"\n  ⚠️  Unlabeled: {pb['ssid']}", fg='yellow')
                            click.echo(f"     ID: {device_id}")
                            if pb.get('channel'):
                                click.echo(f"     Channel: {pb['channel']}")
                            
                            # Prompt for label
                            label_input = click.prompt('     Enter label number (or press Enter to skip)', default='', show_default=False)
                            
                            if label_input.strip():
                                try:
                                    label_num = int(label_input)
                                    device['label'] = label_num
                                    device['name'] = str(label_num)  # Use label as name by default
                                    device['labeled_time'] = datetime.now().isoformat()
                                    needs_update = True
                                    click.secho(f"     ✅ Labeled as: {label_num}", fg='green')
                                except ValueError:
                                    click.secho("     Invalid label number", fg='red')
                        
                        elif not device.get('name') or device.get('name') == str(device.get('label')):
                            # Has label but missing custom name
                            click.secho(f"\n  ⚠️  Missing name: {pb['ssid']} (labeled: {device['label']})", fg='yellow')
                            
                            # Prompt for name
                            name_input = click.prompt('     Enter custom name (or press Enter to keep label as name)', default='', show_default=False)
                            
                            if name_input.strip():
                                device['name'] = name_input.strip()
                                needs_update = True
                                click.secho(f"     ✅ Named: {name_input.strip()}", fg='green')
                        
                        else:
                            # Already labeled and named, just show it's there
                            click.echo(f"  ✓ {device.get('name', pb['ssid'])} (label: {device['label']})")
                        
                        if needs_update:
                            # Save config
                            with open(FLEET_CONFIG, 'w') as f:
                                json.dump(config, f, indent=2)
                
                # Check for disappeared devices
                disappeared = seen_devices - current_scan_ids
                for device_id in disappeared:
                    if device_id in existing_devices:
                        name = existing_devices[device_id].get('name', device_id)
                        click.secho(f"  ❌ Disappeared: {name} (ID: {device_id})", fg='red')
                    seen_devices.remove(device_id)
                
                # No wait - scan immediately again
                
        except KeyboardInterrupt:
            click.echo("\n\nLabeling stopped")
            
            # Summary
            labeled = sum(1 for d in config.get('devices', []) if d.get('label') is not None)
            total = len(config.get('devices', []))
            click.echo(f"\nSummary: {labeled}/{total} devices labeled")
            return
    
    # Original single-device labeling logic
    if not label and not name:
        click.secho("Must specify --label and/or --name", fg='red')
        return
    
    config = manager.load_fleet_config()
    devices = config.get('devices', [])
    
    if not devices:
        click.secho("No devices in fleet config. Run 'pb scan' first.", fg='red')
        return
    
    # Find device
    device = None
    if device_id:
        device = next((d for d in devices if d['device_id'] == device_id), None)
        if not device:
            click.secho(f"Device {device_id} not found", fg='red')
            return
    elif len(devices) == 1:
        # Only one device, use it automatically
        device = devices[0]
    else:
        # Multiple devices, show list
        click.echo("Available devices:")
        for i, d in enumerate(devices, 1):
            existing_label = f" [Label: {d.get('label')}]" if d.get('label') else ""
            existing_name = f" [{d.get('name')}]" if d.get('name') else ""
            click.echo(f"{i}. {d['ssid']} (ID: {d['device_id']}){existing_name}{existing_label}")
        
        choice = click.prompt("Select device to label", type=int) - 1
        if choice < 0 or choice >= len(devices):
            click.secho("Invalid selection", fg='red')
            return
        device = devices[choice]
    
    # Update device
    if label is not None:
        device['label'] = label
        if not name:
            # Use label as name if no custom name provided
            device['name'] = str(label)
    
    if name:
        device['name'] = name
    
    device['labeled_time'] = datetime.now().isoformat()
    
    # Save config
    with open(FLEET_CONFIG, 'w') as f:
        json.dump(config, f, indent=2)
    
    click.secho(f"✅ Labeled {device['ssid']}", fg='green')
    if device.get('name'):
        click.echo(f"   Name: {device['name']}")
    if device.get('label') is not None:
        click.echo(f"   Label: {device['label']}")


@cli.command()
@click.confirmation_option(prompt='Clear all fleet data?')
@click.pass_obj
def clear(manager):
    """Clear fleet configuration"""
    if FLEET_CONFIG.exists():
        FLEET_CONFIG.unlink()
        click.secho("Fleet configuration cleared", fg='green')
    else:
        click.echo("No configuration to clear")


@cli.command()
@click.pass_obj
def status(manager):
    """Show current status and configuration"""
    click.secho("PixelBlaze Fleet Status", fg='cyan', bold=True)
    click.echo("="*40)
    
    # Current network
    current = manager.get_current_network()
    if current:
        click.echo(f"Current WiFi: {current}")
    else:
        click.echo("WiFi: Not connected")
    
    # Config location
    click.echo(f"Config dir: {CONFIG_DIR}")
    click.echo(f"Logs dir: {LOGS_DIR}")
    
    # Fleet status
    config = manager.load_fleet_config()
    if config:
        devices = config.get('devices', [])
        configured = sum(1 for d in devices if d.get('configured'))
        
        click.echo(f"\nFleet: {len(devices)} device(s)")
        click.echo(f"  Configured: {configured}")
        click.echo(f"  Unconfigured: {len(devices) - configured}")
        
        if config.get('last_scan'):
            click.echo(f"  Last scan: {config['last_scan']}")
    else:
        click.echo("\nNo fleet configuration found")
        click.echo("Run 'pb scan' to discover devices")


@cli.command()
@click.option('--days', default=7, help='Delete logs older than N days')
@click.pass_obj
def cleanup(manager, days):
    """Clean up old log files"""
    cutoff = time.time() - (days * 24 * 60 * 60)
    removed = 0
    
    for log_file in LOGS_DIR.glob("pb_*.log"):
        if log_file.stat().st_mtime < cutoff:
            log_file.unlink()
            removed += 1
    
    click.secho(f"Removed {removed} log file(s) older than {days} days", fg='green')


if __name__ == '__main__':
    cli()