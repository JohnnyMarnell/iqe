#!/usr/bin/env python3
"""
ArtNet Receiver and LED Visualizer
Receives ArtNet packets and displays as 420x24 LED grid
"""

import socket
import struct
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import threading
import queue

class ArtNetReceiver:
    def __init__(self, bind_ip="0.0.0.0", port=6455):
        self.bind_ip = bind_ip
        self.port = port
        self.sock = None
        self.running = False
        
        # LED configuration
        self.width = 420
        self.height = 24
        self.pixels_per_universe = 170  # 510 channels / 3
        self.total_pixels = self.width * self.height
        
        # Pixel buffer - initialize to black
        self.pixels = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        self.pixel_lock = threading.Lock()
        
        # Universe mapping
        self.universes = {}
        
    def start(self):
        """Start the ArtNet receiver"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.bind_ip, self.port))
        self.sock.settimeout(0.1)  # Non-blocking with timeout
        self.running = True
        
        print(f"ArtNet receiver listening on {self.bind_ip}:{self.port}")
        
        # Start receiver thread
        self.receiver_thread = threading.Thread(target=self._receive_loop)
        self.receiver_thread.daemon = True
        self.receiver_thread.start()
        
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
        # Check for ArtNet header
        if len(data) < 18:
            return
            
        header = data[0:8]
        if header != b'Art-Net\x00':
            return
            
        # Get OpCode
        opcode = struct.unpack('<H', data[8:10])[0]
        
        # OpOutput (0x5000) is what we want
        if opcode != 0x5000:
            return
            
        # Parse ArtNet packet
        sequence = data[12]
        physical = data[13]
        universe = struct.unpack('<H', data[14:16])[0]
        length = struct.unpack('>H', data[16:18])[0]
        
        # Extract DMX data
        dmx_data = data[18:18+length]
        
        # Store universe data
        self.universes[universe] = {
            'data': dmx_data,
            'addr': addr
        }
        
        # Update pixel buffer
        self._update_pixels(universe, dmx_data)
        
    def _update_pixels(self, universe, dmx_data):
        """Update pixel buffer from DMX data"""
        with self.pixel_lock:
            # Calculate starting pixel for this universe
            start_pixel = universe * self.pixels_per_universe
            
            # Don't overflow our pixel buffer
            if start_pixel >= self.total_pixels:
                return
                
            # Convert DMX to pixels
            pixels_in_universe = min(len(dmx_data) // 3, self.pixels_per_universe)
            end_pixel = min(start_pixel + pixels_in_universe, self.total_pixels)
            
            # Update the pixel buffer
            for i in range(start_pixel, end_pixel):
                dmx_offset = (i - start_pixel) * 3
                if dmx_offset + 2 < len(dmx_data):
                    row = i // self.width
                    col = i % self.width
                    
                    self.pixels[row, col, 0] = dmx_data[dmx_offset]      # R
                    self.pixels[row, col, 1] = dmx_data[dmx_offset + 1]  # G
                    self.pixels[row, col, 2] = dmx_data[dmx_offset + 2]  # B
                    
    def get_pixels(self):
        """Get current pixel buffer"""
        with self.pixel_lock:
            return self.pixels.copy()
            
    def get_stats(self):
        """Get receiver statistics"""
        return {
            'universes_received': len(self.universes),
            'expected_universes': 60,
            'pixels_updated': len(self.universes) * self.pixels_per_universe
        }


class LEDVisualizer:
    def __init__(self, receiver):
        self.receiver = receiver
        
        # Set up the plot
        plt.style.use('dark_background')
        self.fig, self.ax = plt.subplots(figsize=(14, 2))
        self.fig.canvas.manager.set_window_title('ArtNet LED Visualizer - 420x24')
        
        # Initial image
        self.im = self.ax.imshow(
            self.receiver.get_pixels(),
            aspect='auto',
            interpolation='nearest'
        )
        
        # Configure axes
        self.ax.set_title('LED Array Visualization (420 x 24 pixels)')
        self.ax.set_xlabel('Pixel Column')
        self.ax.set_ylabel('Pixel Row')
        
        # Remove tick marks for cleaner look
        self.ax.set_xticks([0, 100, 200, 300, 400])
        self.ax.set_yticks([0, 12, 23])
        
        # Info text
        self.info_text = self.ax.text(
            0.02, 0.98, '', 
            transform=self.ax.transAxes,
            verticalalignment='top',
            fontsize=8,
            color='white',
            bbox=dict(boxstyle='round', facecolor='black', alpha=0.5)
        )
        
    def update(self, frame):
        """Update the visualization"""
        # Get latest pixels
        pixels = self.receiver.get_pixels()
        self.im.set_array(pixels)
        
        # Update info
        stats = self.receiver.get_stats()
        info = f"Universes: {stats['universes_received']}/{stats['expected_universes']}\n"
        info += f"Pixels received: {stats['pixels_updated']}/{self.receiver.total_pixels}"
        self.info_text.set_text(info)
        
        return [self.im, self.info_text]
        
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
    # Create receiver
    receiver = ArtNetReceiver(bind_ip="127.0.0.1", port=6455)  # localhost, custom port
    
    try:
        # Start receiver
        receiver.start()
        
        # Create and start visualizer
        viz = LEDVisualizer(receiver)
        viz.start()  # This blocks until window is closed
        
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        receiver.stop()


if __name__ == "__main__":
    main()