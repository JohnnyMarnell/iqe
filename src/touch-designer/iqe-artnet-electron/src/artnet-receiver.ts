import * as dgram from 'dgram';

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

interface SocketBinding {
  socket: dgram.Socket;
  ip: string;
  port: number;
  name: string;
}

interface ParCanData {
  r: number;
  g: number;
  b: number;
  universe: number;
  channel: number;
  lastUpdate: number;
}

export class ArtNetReceiver {
  private sockets: SocketBinding[] = [];
  private running = false;
  private seenSources = new Set<string>();

  // LED configuration - 420x24 grid
  private readonly width = 420;
  private readonly height = 24;
  private readonly totalPixels = this.width * this.height;

  // Pixel buffer - RGB values
  private pixels: Uint8Array;
  private universes: Map<number, UniverseData> = new Map();
  private universeMap: Map<number, UniverseMapping[]> = new Map();

  // ParCan fixtures data
  private parCans: Map<string, ParCanData> = new Map();

  // Statistics
  private packetCount = 0;
  private lastPacketTime = 0;
  private packetsByUniverse: Map<number, number> = new Map();

  constructor() {
    // Initialize pixel buffer (height x width x 3 for RGB)
    this.pixels = new Uint8Array(this.height * this.width * 3);
    this.buildUniverseMap();
    
    // Initialize ParCan data
    this.parCans.set('parcan1', {
      r: 0, g: 0, b: 0,
      universe: 1,
      channel: 1, // 0-indexed, so channel 2 in DMX
      lastUpdate: 0
    });
    
    this.parCans.set('parcan2', {
      r: 0, g: 0, b: 0,
      universe: 1,
      channel: 8, // 0-indexed, so channel 9 in DMX
      lastUpdate: 0
    });
    
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
        
        // Check ParCan status
        let parCanStatus = '';
        this.parCans.forEach((data, name) => {
          if (data.r > 0 || data.g > 0 || data.b > 0) {
            parCanStatus += ` ${name}:RGB(${data.r},${data.g},${data.b})`;
          }
        });
        
        console.log(`ArtNet status: ${this.packetCount} packets, ${this.universes.size} universes, ${nonZeroPixels} lit pixels${parCanStatus}`);
      }
    }, 2000);
  }

  private buildUniverseMap(): void {
    let currentUniverse = 1; // Main grid starts at universe 1

    for (let row = 0; row < 24; row++) {
      // Apply vertical flip - Row 1 in LX appears at bottom
      const visualRow = 23 - row;

      // Based on actual data pattern for PixLite controller:
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
    // Default binding for main LED grid (PixLite controller)
    this.addSocketBinding('0.0.0.0', 6454, 'Main LED Grid');
    
    // Additional binding for ParCan controller if needed
    // Note: Usually one port can receive from multiple controllers
    // but we can add multiple bindings if needed
    // this.addSocketBinding('0.0.0.0', 6455, 'ParCan Controller');
    
    this.running = true;
  }

  private addSocketBinding(ip: string, port: number, name: string): void {
    const socket = dgram.createSocket('udp4');
    
    socket.on('message', (data, rinfo) => {
      // Log first packet from each unique source
      const sourceKey = `${rinfo.address}:${rinfo.port}`;
      if (!this.seenSources.has(sourceKey)) {
        this.seenSources.add(sourceKey);
        const controllerName = 
          rinfo.address === '10.10.42.68' ? 'Pknight ParCan Controller' :
          rinfo.address === '10.10.42.80' ? 'PixLite LED Controller' :
          rinfo.address === '127.0.0.1' ? 'Localhost (Test)' :
          'Unknown Controller';
        console.log(`${name}: First packet from ${controllerName} at ${rinfo.address}:${rinfo.port}, size: ${data.length}`);
      }
      this.processArtNetPacket(data, rinfo.address, name);
    });

    socket.on('error', (err) => {
      console.error(`${name} ArtNet error:`, err);
    });

    socket.on('listening', () => {
      const address = socket.address();
      console.log(`${name} listening on ${address.address}:${address.port}`);
    });

    socket.bind(port, ip, () => {
      console.log(`${name} bound to ${ip}:${port}`);
    });

    this.sockets.push({ socket, ip, port, name });
  }

  stop(): void {
    this.running = false;
    for (const binding of this.sockets) {
      binding.socket.close();
    }
    this.sockets = [];
  }

  private processArtNetPacket(data: Buffer, addr: string, source: string): void {
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

    // Route based on source IP address
    // ParCan controller is at 10.10.42.68
    // PixLite controller is at 10.10.42.80
    if (addr === '10.10.42.68' && universe === 1) {
      // ParCan data from Pknight controller
      this.updateParCans(dmxData);
    } else if (addr === '10.10.42.80' || addr === '127.0.0.1') {
      // Main LED grid data from PixLite controller (or localhost for testing)
      this.updatePixelsMapped(universe, dmxData);
    } else {
      // Unknown source, try to process as main grid
      this.updatePixelsMapped(universe, dmxData);
    }
  }

  private updateParCans(dmxData: Buffer): void {
    const currentTime = Date.now();
    
    // Update each ParCan
    this.parCans.forEach((parCan, name) => {
      if (parCan.universe === 1) {
        const channelStart = parCan.channel;
        
        // Make sure we have enough data
        if (dmxData.length > channelStart + 2) {
          parCan.r = dmxData[channelStart];
          parCan.g = dmxData[channelStart + 1];
          parCan.b = dmxData[channelStart + 2];
          parCan.lastUpdate = currentTime;
          
          // Log significant changes
          if (parCan.r > 10 || parCan.g > 10 || parCan.b > 10) {
            if (this.packetCount % 30 === 0) { // Log every second at 30fps
              console.log(`${name}: RGB(${parCan.r}, ${parCan.g}, ${parCan.b})`);
            }
          }
        }
      }
    });
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

  getParCans(): Map<string, ParCanData> {
    return this.parCans;
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

    // Get expected universes (universe 1 is shared between ParCans and main grid)
    const expectedUniverses = Array.from(this.universeMap.keys());
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

  setConfig(config: { spacedRows?: boolean }): void {
    // Configuration can be extended here
  }
}