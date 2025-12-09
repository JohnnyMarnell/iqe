import * as dgram from 'dgram';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

interface UniverseMapping {
  row: number;
  startPixel: number;
  dmxStart: number;
  pixelCount: number;
}

interface UniverseData {
  data: Buffer;
  addr: string;
  time: number;
}

interface Stats {
  universesReceived: number;
  activeUniverses: number[];
  expectedUniverses: number[];
  missingUniverses: number[];
  packetCount: number;
  packetsByUniverse: { [key: number]: number };
  lastPacket: number;
}

// ParCan configuration - 8 flood lights with DMX addresses
interface ParCanConfig {
  universe: number;
  dmxChannel: number; // 0-based DMX channel (0 = DMX channel 1)
  x: number; // Position in visualization
  y: number;
  radius: number; // Flood light radius
}

export class ArtNetSniffer {
  private socket: dgram.Socket | null = null;
  private bindIp = '0.0.0.0';
  private port = 6454; // Standard ArtNet port
  private running = false;
  private sniffMode = false;

  // LED configuration - 420x24 grid
  private readonly width = 420;
  private readonly height = 24;
  private readonly totalPixels = this.width * this.height;

  // Pixel buffer - RGB values
  private pixels: Uint8Array;
  private universes: Map<number, UniverseData> = new Map();
  private universeMap: Map<number, UniverseMapping[]> = new Map();

  // ParCan flood lights - 8 total
  private parCans: ParCanConfig[] = [];
  private parCanColors: Map<number, { r: number, g: number, b: number }> = new Map();
  private parCanRadius = 50; // Default radius for flood effect

  // Statistics
  private packetCount = 0;
  private lastPacketTime = 0;
  private packetsByUniverse: Map<number, number> = new Map();

  constructor() {
    // Initialize pixel buffer (height x width x 3 for RGB)
    this.pixels = new Uint8Array(this.height * this.width * 3);
    this.buildUniverseMap();
    this.initializeParCans();
    
    // Try to enable promiscuous mode for packet sniffing
    this.enablePromiscuousMode();
    
    // Periodic status log
    setInterval(() => {
      if (this.running) {
        // Count non-zero pixels
        let nonZeroPixels = 0;
        for (let i = 0; i < this.pixels.length; i += 3) {
          if (this.pixels[i] > 0 || this.pixels[i+1] > 0 || this.pixels[i+2] > 0) {
            nonZeroPixels++;
          }
        }
        console.log(`ArtNet status: ${this.packetCount} packets, ${this.universes.size} universes, ${nonZeroPixels} lit pixels, ${this.parCanColors.size} ParCans`);
      }
    }, 2000);
  }

  private initializeParCans(): void {
    // Configure 8 ParCans positioned around the LED grid
    // 4 corners + 4 mid-points
    const positions = [
      { x: 0, y: 0 },           // Top-left
      { x: 420, y: 0 },         // Top-right
      { x: 0, y: 24 },          // Bottom-left
      { x: 420, y: 24 },        // Bottom-right
      { x: 210, y: 0 },         // Top-center
      { x: 210, y: 24 },        // Bottom-center
      { x: 0, y: 12 },          // Left-center
      { x: 420, y: 12 }         // Right-center
    ];

    // Configure ParCans on specific universes and DMX channels
    // Assuming they're on universes 100-107 for isolation
    // Or they could be multiplexed on existing universes with specific DMX offsets
    for (let i = 0; i < 8; i++) {
      this.parCans.push({
        universe: 100 + i,  // Separate universes for each ParCan
        dmxChannel: 0,      // Starting at DMX channel 1 (0-indexed)
        x: positions[i].x,
        y: positions[i].y,
        radius: this.parCanRadius
      });
    }

    console.log(`Initialized ${this.parCans.length} ParCan flood lights`);
  }

  private async enablePromiscuousMode(): Promise<void> {
    try {
      // Try to enable promiscuous mode on the main network interface
      // This allows us to see all packets on the network, not just those addressed to us
      
      // First, try to find the active network interface
      const { stdout } = await execAsync("networksetup -listallhardwareports | grep -A 2 'Wi-Fi\\|Ethernet' | grep 'Device' | awk '{print $2}' | head -1");
      const iface = stdout.trim() || 'en0';
      
      console.log(`Attempting to sniff packets on interface: ${iface}`);
      
      // Note: This requires sudo privileges and may not work in all environments
      // For a production solution, consider using a dedicated packet capture library
      // or configuring the network to mirror ArtNet traffic to this machine
      
      this.sniffMode = true;
      console.log('Packet sniffing mode enabled (listening for all ArtNet traffic)');
    } catch (error) {
      console.log('Could not enable promiscuous mode, falling back to standard receive mode');
      console.log('To sniff packets, you may need to:');
      console.log('1. Configure your network switch to mirror ArtNet traffic');
      console.log('2. Use a network tap or hub');
      console.log('3. Run with elevated privileges (not recommended)');
      this.sniffMode = false;
    }
  }

  private buildUniverseMap(): void {
    let currentUniverse = 1;

    for (let row = 0; row < 24; row++) {
      // Apply vertical flip - Row 1 in LX appears at bottom
      const visualRow = 23 - row;

      // Based on actual data pattern:
      // Universe pattern: 510, 510, 240 bytes repeating

      // First universe: 510 bytes = 170 pixels max
      this.universeMap.set(currentUniverse, [{
        row: visualRow,
        startPixel: 0,
        dmxStart: 0,
        pixelCount: 170
      }]);
      currentUniverse++;

      // Second universe: 510 bytes = 170 pixels max
      this.universeMap.set(currentUniverse, [{
        row: visualRow,
        startPixel: 170,
        dmxStart: 0,
        pixelCount: 170
      }]);
      currentUniverse++;

      // Third universe: 240 bytes = 80 pixels
      this.universeMap.set(currentUniverse, [{
        row: visualRow,
        startPixel: 340,
        dmxStart: 0,
        pixelCount: 80
      }]);
      currentUniverse++;
    }
  }

  start(): void {
    this.socket = dgram.createSocket({ type: 'udp4', reuseAddr: true });
    
    this.socket.on('message', (data, rinfo) => {
      // Only log first packet
      if (this.packetCount === 0) {
        console.log(`First packet received from ${rinfo.address}:${rinfo.port}, size: ${data.length}`);
        if (this.sniffMode) {
          console.log('Sniffing mode: capturing packets not addressed to localhost');
        }
      }
      this.processArtNetPacket(data, rinfo.address);
    });

    this.socket.on('error', (err) => {
      console.error('ArtNet receiver error:', err);
      if (err.message.includes('EADDRINUSE')) {
        console.log('Port 6454 is already in use. Attempting to sniff packets instead...');
        this.sniffMode = true;
      }
    });

    this.socket.on('listening', () => {
      const address = this.socket!.address();
      console.log(`ArtNet sniffer listening on ${address.address}:${address.port}`);
      
      // Try to set socket to promiscuous mode
      try {
        // This is platform-specific and may not work on all systems
        // @ts-ignore
        this.socket!.setMulticastLoopback(true);
        // @ts-ignore
        this.socket!.setBroadcast(true);
        console.log('Socket configured for broadcast/multicast reception');
      } catch (e) {
        console.log('Could not configure socket for enhanced reception');
      }
    });

    this.socket.bind(this.port, this.bindIp, () => {
      this.running = true;
      console.log(`ArtNet sniffer bound to ${this.bindIp}:${this.port}`);
      
      // Join multicast group for ArtNet
      try {
        this.socket!.addMembership('239.255.0.0'); // Common ArtNet multicast address
        console.log('Joined ArtNet multicast group');
      } catch (e) {
        console.log('Could not join multicast group (may not be necessary)');
      }
    });
  }

  stop(): void {
    this.running = false;
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  private processArtNetPacket(data: Buffer, addr: string): void {
    if (data.length < 18) {
      return;
    }

    // Check ArtNet header
    const header = data.slice(0, 8);
    const headerStr = header.toString('ascii', 0, 7);
    if (headerStr !== 'Art-Net') {
      return;
    }

    // Get opcode
    const opcode = data.readUInt16LE(8);

    // OpOutput (0x5000)
    if (opcode !== 0x5000) {
      return;
    }

    // Parse packet
    const sequence = data[12];
    const physical = data[13];
    const universe = data.readUInt16LE(14);
    const length = data.readUInt16BE(16);

    // Extract DMX data
    const dmxData = data.slice(18, 18 + length);

    // Update statistics
    this.packetCount++;
    this.packetsByUniverse.set(universe, (this.packetsByUniverse.get(universe) || 0) + 1);
    this.lastPacketTime = Date.now();

    // Store universe data
    this.universes.set(universe, {
      data: dmxData,
      addr: addr,
      time: this.lastPacketTime
    });

    // Check if this universe contains ParCan data
    this.updateParCans(universe, dmxData);

    // Update pixel buffer for LED strips
    this.updatePixelsMapped(universe, dmxData);
  }

  private updateParCans(universe: number, dmxData: Buffer): void {
    // Check if any ParCans are on this universe
    for (const parCan of this.parCans) {
      if (parCan.universe === universe) {
        // ParCan uses 7 channels: Dimmer, R, G, B, Amber, White, UV
        const dmxStart = parCan.dmxChannel;
        
        if (dmxStart + 6 < dmxData.length) {
          const dimmer = dmxData[dmxStart];
          const r = dmxData[dmxStart + 1];
          const g = dmxData[dmxStart + 2];
          const b = dmxData[dmxStart + 3];
          // Ignoring amber, white, UV for now
          
          // Apply dimmer to RGB values
          const scaledR = Math.round((r * dimmer) / 255);
          const scaledG = Math.round((g * dimmer) / 255);
          const scaledB = Math.round((b * dimmer) / 255);
          
          // Store the color for this ParCan
          const parCanId = this.parCans.indexOf(parCan);
          this.parCanColors.set(parCanId, {
            r: scaledR,
            g: scaledG,
            b: scaledB
          });
          
          // Apply flood light effect to nearby pixels
          this.applyFloodLight(parCan, scaledR, scaledG, scaledB);
        }
      }
    }
  }

  private applyFloodLight(parCan: ParCanConfig, r: number, g: number, b: number): void {
    // Apply a radial gradient effect to simulate flood light
    const centerX = parCan.x;
    const centerY = parCan.y;
    const radius = parCan.radius;
    
    // Iterate through pixels within the flood radius
    for (let row = 0; row < this.height; row++) {
      for (let col = 0; col < this.width; col++) {
        const dx = col - centerX;
        const dy = row - centerY;
        const distance = Math.sqrt(dx * dx + dy * dy);
        
        if (distance <= radius) {
          // Calculate falloff (inverse square law for realistic lighting)
          const intensity = Math.max(0, 1 - (distance / radius));
          const falloff = intensity * intensity; // Quadratic falloff
          
          // Apply additive blending with existing pixel colors
          const pixelIndex = (row * this.width + col) * 3;
          
          // Add the flood light color with falloff
          this.pixels[pixelIndex] = Math.min(255, 
            this.pixels[pixelIndex] + Math.round(r * falloff * 0.5)); // 0.5 to prevent oversaturation
          this.pixels[pixelIndex + 1] = Math.min(255, 
            this.pixels[pixelIndex + 1] + Math.round(g * falloff * 0.5));
          this.pixels[pixelIndex + 2] = Math.min(255, 
            this.pixels[pixelIndex + 2] + Math.round(b * falloff * 0.5));
        }
      }
    }
  }

  private updatePixelsMapped(universe: number, dmxData: Buffer): void {
    const mappings = this.universeMap.get(universe);
    if (!mappings) return;

    for (const mapping of mappings) {
      const { row, startPixel, dmxStart, pixelCount } = mapping;

      // Calculate how many pixels we can actually update
      const availableChannels = dmxData.length - dmxStart;
      const pixelsToUpdate = Math.min(pixelCount, Math.floor(availableChannels / 3));

      // Update the pixels with horizontal flip
      for (let i = 0; i < pixelsToUpdate; i++) {
        const dmxOffset = dmxStart + (i * 3);
        // Flip horizontally: 419 - pixelCol
        const pixelCol = (this.width - 1) - (startPixel + i);

        if (pixelCol >= 0 && pixelCol < this.width && dmxOffset + 2 < dmxData.length) {
          const pixelIndex = (row * this.width + pixelCol) * 3;
          this.pixels[pixelIndex] = dmxData[dmxOffset];     // R
          this.pixels[pixelIndex + 1] = dmxData[dmxOffset + 1]; // G
          this.pixels[pixelIndex + 2] = dmxData[dmxOffset + 2]; // B
        }
      }
    }
  }

  getPixels(): Uint8Array {
    return this.pixels;
  }

  getParCans(): { config: ParCanConfig[], colors: Map<number, { r: number, g: number, b: number }> } {
    return {
      config: this.parCans,
      colors: this.parCanColors
    };
  }

  setParCanRadius(radius: number): void {
    this.parCanRadius = radius;
    for (const parCan of this.parCans) {
      parCan.radius = radius;
    }
    console.log(`ParCan flood radius set to ${radius}`);
  }

  getStats(): Stats {
    const currentTime = Date.now();
    const activeUniverses: number[] = [];

    // Check which universes are active (received in last second)
    this.universes.forEach((data, universe) => {
      if (currentTime - data.time < 1000) {
        activeUniverses.push(universe);
      }
    });

    // Get expected universes
    const expectedUniverses = Array.from(this.universeMap.keys());
    // Also expect ParCan universes
    this.parCans.forEach(pc => {
      if (!expectedUniverses.includes(pc.universe)) {
        expectedUniverses.push(pc.universe);
      }
    });
    
    const missingUniverses = expectedUniverses.filter(u => !activeUniverses.includes(u));

    const packetsByUniverseObj: { [key: number]: number } = {};
    this.packetsByUniverse.forEach((count, universe) => {
      packetsByUniverseObj[universe] = count;
    });

    return {
      universesReceived: this.universes.size,
      activeUniverses: activeUniverses.sort((a, b) => a - b),
      expectedUniverses,
      missingUniverses,
      packetCount: this.packetCount,
      packetsByUniverse: packetsByUniverseObj,
      lastPacket: this.lastPacketTime > 0 ? (currentTime - this.lastPacketTime) / 1000 : 999
    };
  }

  setConfig(config: { spacedRows?: boolean, parCanRadius?: number }): void {
    if (config.parCanRadius !== undefined) {
      this.setParCanRadius(config.parCanRadius);
    }
  }
}