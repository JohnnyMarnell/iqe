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

export class ArtNetReceiver {
  private socket: dgram.Socket | null = null;
  private bindIp = '0.0.0.0';
  private port = 6454; // Standard ArtNet port
  private running = false;

  // LED configuration - 420x24 grid
  private readonly width = 420;
  private readonly height = 24;
  private readonly totalPixels = this.width * this.height;

  // Pixel buffer - RGB values
  private pixels: Uint8Array;
  private universes: Map<number, UniverseData> = new Map();
  private universeMap: Map<number, UniverseMapping[]> = new Map();

  // Statistics
  private packetCount = 0;
  private lastPacketTime = 0;
  private packetsByUniverse: Map<number, number> = new Map();

  constructor() {
    // Initialize pixel buffer (height x width x 3 for RGB)
    this.pixels = new Uint8Array(this.height * this.width * 3);
    this.buildUniverseMap();
    
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
        console.log(`ArtNet status: ${this.packetCount} packets, ${this.universes.size} universes, ${nonZeroPixels} lit pixels`);
      }
    }, 2000);
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
    this.socket = dgram.createSocket('udp4');
    
    this.socket.on('message', (data, rinfo) => {
      // Only log first packet
      if (this.packetCount === 0) {
        console.log(`First packet received from ${rinfo.address}:${rinfo.port}, size: ${data.length}`);
      }
      this.processArtNetPacket(data, rinfo.address);
    });

    this.socket.on('error', (err) => {
      console.error('ArtNet receiver error:', err);
    });

    this.socket.on('listening', () => {
      const address = this.socket!.address();
      console.log(`ArtNet receiver listening on ${address.address}:${address.port}`);
    });

    this.socket.bind(this.port, this.bindIp, () => {
      this.running = true;
      console.log(`ArtNet receiver bound to ${this.bindIp}:${this.port}`);
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

    // Update pixel buffer
    this.updatePixelsMapped(universe, dmxData);
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