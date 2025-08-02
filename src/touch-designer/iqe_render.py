#!/usr/bin/env python3
"""
IQE ArtNet Receiver and LED Visualizer
Receives ArtNet packets and displays as 420x24 LED grid
With proper universe mapping from LX Studio and PixLite configuration
"""

import socket
import struct
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import threading
import time
from collections import defaultdict

class IQEArtNetReceiver:
    def __init__(self, bind_ip="0.0.0.0", port=7890):
        self.bind_ip = bind_ip
        self.port = port
        self.sock = None
        self.running = False
        
        # LED configuration - 420x24 grid
        self.width = 420
        self.height = 24
        self.total_pixels = self.width * self.height
        
        # Each strip has 140 pixels, 3 strips per row
        self.pixels_per_strip = 140
        self.strips_per_row = 3
        
        # Pixel buffer - initialize to black
        self.pixels = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.pixel_lock = threading.Lock()
        
        # Universe tracking
        self.universes = {}
        self.universe_map = self._build_universe_map()
        
        # Statistics
        self.packet_count = 0
        self.last_packet_time = 0
        self.packets_by_universe = defaultdict(int)
        
    def _build_universe_map(self):
        """Build the universe mapping based on LX Studio configuration"""
        universe_map = {}
        
        # Based on actual ArtNet data being sent:
        # Universe 0: 486 bytes (162 pixels) - contains strip 1 + part of strip 2
        # Universe 1: 378 bytes (126 pixels) - contains rest of strip 2 + strip 3  
        # Universe 2: Not mapped (might be unused)
        # Universe 3: 378 bytes - row 2, strips 1-2
        
        # Let's map based on what we're actually seeing:
        # Each universe seems to contain ~160-170 pixels worth of data
        # 420 pixels per row = 1260 channels
        # Spread across ~2.5 universes per row
        
        # Based on LX Studio actual configuration (0-based universe numbers):
        # Row 1: universes 0,0,1 (strips at DMX 0,420,330)
        # Row 2: universes 3,3,4 (strips at DMX 0,420,330)
        # Pattern: skip 2, so next is 6,6,7 then 9,9,10 etc
        
        universe_map = {}
        
        # Map based on actual LX Studio configuration
        rafter_configs = [
            # (row, universe1, universe2, universe3)
            (0, 0, 0, 1),    # Rafter 1
            (1, 3, 3, 4),    # Rafter 2
            (2, 6, 6, 7),    # Rafter 3
            (3, 9, 9, 10),   # Rafter 4
            (4, 12, 12, 13), # Rafter 5
            (5, 15, 15, 16), # Rafter 6
            (6, 18, 18, 19), # Rafter 7
            (7, 21, 21, 22), # Rafter 8
            (8, 24, 24, 25), # Rafter 9
            (9, 27, 27, 28), # Rafter 10
            (10, 30, 30, 31), # Rafter 11
            (11, 33, 33, 34), # Rafter 12
            (12, 36, 36, 37), # Rafter 13
            (13, 39, 39, 40), # Rafter 14
            (14, 42, 42, 43), # Rafter 15
            (15, 45, 45, 46), # Rafter 16
            (16, 48, 48, 49), # Rafter 17
            (17, 51, 51, 52), # Rafter 18
            (18, 54, 54, 55), # Rafter 19
            (19, 57, 57, 58), # Rafter 20
            (20, 60, 60, 61), # Rafter 21
            (21, 63, 63, 64), # Rafter 22
            (22, 66, 66, 67), # Rafter 23
            (23, 69, 69, 70), # Rafter 24
        ]
        
        # Based on LX fixture configuration with DMX universe limitations:
        # Row pattern (e.g., Rafter 1):
        # - Strip 1: Universe 1, DMX 0-419 (140 pixels)
        # - Strip 2: Universe 1, DMX 420-511 (31 pixels) + Universe 2, DMX 0-329 (109 pixels)
        # - Strip 3: Universe 2, DMX 330-749 (140 pixels)
        
        # But LX might be linearizing this differently. Based on actual data:
        # - We're receiving universes 1-72 (not the config pattern)
        # - Only 330 pixels are lit per row
        
        # Let's map based on what we're actually receiving
        # The pattern appears to be that LX is only sending 330 pixels per row
        # spread across 3 universes
        
        current_universe = 1
        
        for row in range(24):  # 24 rows
            # Based on actual data received:
            # First universe: 80 pixels
            universe_map[current_universe] = [{
                'row': row,
                'start_pixel': 0,
                'dmx_start': 0,
                'pixel_count': 80
            }]
            current_universe += 1
            
            # Second universe: 170 pixels
            universe_map[current_universe] = [{
                'row': row,
                'start_pixel': 80,
                'dmx_start': 0,
                'pixel_count': 170
            }]
            current_universe += 1
            
            # Third universe: 80 pixels
            universe_map[current_universe] = [{
                'row': row,
                'start_pixel': 250,
                'dmx_start': 0,
                'pixel_count': 80
            }]
            current_universe += 1
        
        return universe_map
        
    def start(self):
        """Start the ArtNet receiver"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.bind_ip, self.port))
        self.sock.settimeout(0.1)
        self.running = True
        
        print(f"IQE ArtNet receiver listening on {self.bind_ip}:{self.port}")
        print(f"Mapped universes: {sorted(list(self.universe_map.keys()))[:20]}...")
        print("-" * 60)
        
        self.receiver_thread = threading.Thread(target=self._receive_loop)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()
        
        # Start summary thread
        self.summary_thread = threading.Thread(target=self._summary_loop)
        self.summary_thread.daemon = True
        self.summary_thread.start()
    
    def _summary_loop(self):
        """Print summary every 5 seconds"""
        while self.running:
            time.sleep(5)
            stats = self.get_stats()
            print(f"\n--- Summary: Active universes: {sorted(stats['active_universes'])} ---\n")
        
    def stop(self):
        """Stop the receiver"""
        self.running = False
        if self.sock:
            self.sock.close()
            
    def _receive_loop(self):
        """Main receive loop"""
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
                self._process_artnet_packet(data, addr)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Receive error: {e}")
                
    def _process_artnet_packet(self, data, addr):
        """Process incoming ArtNet packet"""
        if len(data) < 18:
            return
            
        header = data[0:8]
        if header != b'Art-Net\x00':
            return
            
        opcode = struct.unpack('<H', data[8:10])[0]
        
        # OpOutput (0x5000)
        if opcode != 0x5000:
            return
            
        # Parse ArtNet packet
        sequence = data[12]
        physical = data[13]
        universe = struct.unpack('<H', data[14:16])[0]
        length = struct.unpack('>H', data[16:18])[0]
        
        # Extract DMX data
        dmx_data = data[18:18+length]
        
        # Update statistics
        self.packet_count += 1
        self.packets_by_universe[universe] += 1
        self.last_packet_time = time.time()
        
        # Store universe data
        self.universes[universe] = {
            'data': dmx_data,
            'addr': addr,
            'time': self.last_packet_time
        }
        
        # Update pixel buffer using our mapping
        self._update_pixels_mapped(universe, dmx_data)
        
    def _update_pixels_mapped(self, universe, dmx_data):
        """Update pixel buffer using the universe mapping"""
        if universe not in self.universe_map:
            return
            
        with self.pixel_lock:
            for mapping in self.universe_map[universe]:
                row = mapping['row']
                start_pixel = mapping['start_pixel']
                dmx_start = mapping['dmx_start']
                pixel_count = mapping['pixel_count']
                
                # Calculate how many pixels we can actually update
                available_channels = len(dmx_data) - dmx_start
                pixels_to_update = min(pixel_count, available_channels // 3)
                
                # Remove debug for now
                pass
                
                # Update the pixels
                pixels_actually_updated = 0
                for i in range(pixels_to_update):
                    dmx_offset = dmx_start + (i * 3)
                    pixel_col = start_pixel + i
                    
                    if pixel_col < self.width and dmx_offset + 2 < len(dmx_data):
                        self.pixels[row, pixel_col, 0] = dmx_data[dmx_offset]      # R
                        self.pixels[row, pixel_col, 1] = dmx_data[dmx_offset + 1]  # G
                        self.pixels[row, pixel_col, 2] = dmx_data[dmx_offset + 2]  # B
                        pixels_actually_updated += 1
                    elif pixel_col >= self.width:
                        print(f"WARNING: Pixel column {pixel_col} exceeds width {self.width} (universe {universe}, row {row})")
                
                if universe == 3 and pixels_actually_updated < pixels_to_update:
                    print(f"U{universe}: Only updated {pixels_actually_updated} of {pixels_to_update} pixels")
                    
    def get_pixels(self):
        """Get current pixel buffer"""
        with self.pixel_lock:
            # Debug: check which pixels are non-zero
            if hasattr(self, '_debug_counter'):
                self._debug_counter += 1
            else:
                self._debug_counter = 0
                
            if self._debug_counter % 100 == 0:  # Every 100 frames
                for row in range(min(2, self.height)):  # Check first 2 rows
                    non_zero = np.where(np.any(self.pixels[row] != 0, axis=1))[0]
                    if len(non_zero) > 0:
                        print(f"Row {row}: pixels {non_zero[0]}-{non_zero[-1]} are lit ({len(non_zero)} pixels)")
                    
            return self.pixels.copy()
            
    def get_stats(self):
        """Get receiver statistics"""
        current_time = time.time()
        
        # Check which universes are active
        active_universes = []
        for univ_id, univ_data in self.universes.items():
            if current_time - univ_data.get('time', 0) < 1.0:
                active_universes.append(univ_id)
        
        # Count unique universes we expect
        expected_universes = sorted(self.universe_map.keys())
        
        return {
            'universes_received': len(self.universes),
            'active_universes': active_universes,
            'expected_universes': expected_universes,
            'missing_universes': [u for u in expected_universes if u not in active_universes],
            'packet_count': self.packet_count,
            'packets_by_universe': dict(self.packets_by_universe),
            'last_packet': current_time - self.last_packet_time if self.last_packet_time > 0 else 999
        }


class IQELEDVisualizer:
    def __init__(self, receiver, spaced_rows=False, pixel_shift=0):
        self.receiver = receiver
        self.spaced_rows = spaced_rows
        self.pixel_shift = pixel_shift
        
        # Calculate display dimensions
        if spaced_rows:
            # Real world: 25' x 21' = 420 pixels x 353 pixels (maintaining aspect ratio)
            # 24 rows need to fit in ~353 pixels with 23 gaps
            # (353 - 24) / 23 = ~14 pixels per gap
            self.row_height = 1  # Each row is 1 pixel tall
            self.row_gap = 14    # 14 pixels between rows
            self.display_height = 24 * self.row_height + 23 * self.row_gap  # = 24 + 322 = 346
        else:
            self.display_height = 24
            self.row_height = 1
            self.row_gap = 0
            
        # Create display buffer
        self.display_pixels = np.zeros((self.display_height, 420, 3), dtype=np.uint8)
        
        # Set up the plot
        plt.style.use('dark_background')
        if spaced_rows:
            # Make figure more square to match real aspect ratio
            fig_width = 14
            fig_height = int(14 * (self.display_height / 420)) + 2  # Add space for stats
            self.fig, (self.ax_main, self.ax_stats) = plt.subplots(
                2, 1, figsize=(fig_width, fig_height), 
                gridspec_kw={'height_ratios': [self.display_height, 40]}
            )
        else:
            self.fig, (self.ax_main, self.ax_stats) = plt.subplots(
                2, 1, figsize=(14, 4), 
                gridspec_kw={'height_ratios': [3, 1]}
            )
        self.fig.canvas.manager.set_window_title('IQE ArtNet LED Visualizer - 420x24')
        
        # Main LED display
        self.im = self.ax_main.imshow(
            self.display_pixels,
            aspect='equal' if spaced_rows else 'auto',
            interpolation='nearest'
        )
        
        # Configure main axes
        title = 'IQE LED Ceiling Array (420 x 24 pixels, 24 rows x 3 strips x 140 pixels)'
        if spaced_rows:
            title += f' - Realistic Spacing (25\' x 21\' = 420 x {self.display_height} pixels)'
        self.ax_main.set_title(title)
        self.ax_main.set_xlabel('Pixel Column')
        self.ax_main.set_ylabel('Row (Rafter)')
        
        # Set ticks to show strip boundaries
        self.ax_main.set_xticks([0, 140, 280, 419])
        self.ax_main.set_xticklabels(['0', '140\nStrip 1', '280\nStrip 2', '419\nEnd'])
        
        # Ensure we show the full pixel range
        self.ax_main.set_xlim(-0.5, 419.5)  # Show pixels 0-419
        
        if spaced_rows:
            # Show fewer Y ticks for spaced view
            y_positions = [i * (self.row_height + self.row_gap) + self.row_height // 2 for i in range(0, 24, 4)]
            self.ax_main.set_yticks(y_positions)
            self.ax_main.set_yticklabels([f'Row {i}' for i in range(0, 24, 4)])
        else:
            self.ax_main.set_yticks(list(range(0, 24, 3)))
        
        # Stats display
        self.ax_stats.axis('off')
        self.stats_text = self.ax_stats.text(
            0.02, 0.5, '', 
            transform=self.ax_stats.transAxes,
            verticalalignment='center',
            fontsize=8,
            color='white',
            family='monospace'
        )
        
    def update(self, frame):
        """Update the visualization"""
        # Get latest pixels
        pixels = self.receiver.get_pixels()
        
        # Apply pixel shift if requested
        if self.pixel_shift != 0:
            shifted_pixels = np.zeros_like(pixels)
            for row in range(pixels.shape[0]):
                if self.pixel_shift > 0:
                    # Shift right
                    shifted_pixels[row, self.pixel_shift:] = pixels[row, :-self.pixel_shift]
                else:
                    # Shift left
                    shifted_pixels[row, :self.pixel_shift] = pixels[row, -self.pixel_shift:]
            pixels = shifted_pixels
        
        if self.spaced_rows:
            # Copy pixels to display buffer with spacing
            for row in range(24):
                display_row = row * (self.row_height + self.row_gap)
                for r in range(self.row_height):
                    self.display_pixels[display_row + r] = pixels[row]
        else:
            self.display_pixels = pixels
            
        self.im.set_array(self.display_pixels)
        
        # Update stats
        stats = self.receiver.get_stats()
        
        # Format universe info
        active = stats['active_universes']
        expected = stats['expected_universes']
        missing = stats['missing_universes']
        
        info = f"Active Universes: {len(active)}/{len(expected)} - {active[:10]}{'...' if len(active) > 10 else ''}\n"
        if missing:
            info += f"Missing Universes: {missing[:10]}{'...' if len(missing) > 10 else ''}\n"
        else:
            info += "All expected universes active! ✓\n"
        
        info += f"Total Packets: {stats['packet_count']} | Last: {stats['last_packet']:.1f}s ago\n"
        
        # Show packet distribution for top universes
        if stats['packets_by_universe']:
            top_universes = sorted(stats['packets_by_universe'].items(), 
                                 key=lambda x: x[1], reverse=True)[:5]
            info += "Top universes by packets: " + ", ".join(
                f"U{u}:{c}" for u, c in top_universes
            )
        
        self.stats_text.set_text(info)
        
        return [self.im, self.stats_text]
        
    def start(self):
        """Start the visualization"""
        # Animation - update every 50ms (20 FPS)
        self.anim = FuncAnimation(
            self.fig, self.update, 
            interval=50, blit=True
        )
        
        plt.tight_layout()
        plt.show()


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='IQE ArtNet LED Visualizer')
    parser.add_argument('--ip', default='0.0.0.0', help='IP to bind to (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=7890, help='Port to listen on (default: 7890 - LX Studio custom port)')
    parser.add_argument('--spaced', action='store_true', help='Show rows with spacing to reflect real-world geometry')
    parser.add_argument('--shift', type=int, default=0, help='Shift pixels right by N positions (use negative to shift left)')
    args = parser.parse_args()
    
    # Create receiver
    receiver = IQEArtNetReceiver(bind_ip=args.ip, port=args.port)
    
    print("=" * 60)
    print("IQE ArtNet LED Visualizer - 420x24 pixels")
    print("24 rows (rafters) x 3 strips x 140 pixels each")
    if args.spaced:
        print("SPACED MODE: Showing rows with gaps to reflect real geometry")
    print("=" * 60)
    print(f"Listening on {receiver.bind_ip}:{receiver.port}")
    print("-" * 60)
    
    try:
        # Start receiver
        receiver.start()
        
        # Create and start visualizer
        viz = IQELEDVisualizer(receiver, spaced_rows=args.spaced, pixel_shift=args.shift)
        viz.start()  # This blocks until window is closed
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        receiver.stop()
        
        # Print final statistics
        stats = receiver.get_stats()
        print("\nFinal Statistics:")
        print(f"Total packets received: {stats['packet_count']}")
        print(f"Universes seen: {sorted(stats['universes_received'])}")
        if stats['packets_by_universe']:
            print("\nPackets per universe:")
            for u in sorted(stats['packets_by_universe'].keys()):
                print(f"  Universe {u}: {stats['packets_by_universe'][u]} packets")


if __name__ == "__main__":
    main()