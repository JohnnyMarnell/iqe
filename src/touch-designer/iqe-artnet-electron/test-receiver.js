const dgram = require('dgram');

class SimpleArtNetReceiver {
  constructor() {
    this.socket = dgram.createSocket('udp4');
    this.packetCount = 0;
    this.universes = new Set();
  }

  start() {
    this.socket.on('message', (data, rinfo) => {
      if (data.length >= 18 && data.slice(0, 7).toString() === 'Art-Net') {
        const opcode = data.readUInt16LE(8);
        if (opcode === 0x5000) {
          const universe = data.readUInt16LE(14);
          this.universes.add(universe);
          this.packetCount++;
          
          if (this.packetCount % 100 === 1) {
            console.log(`Packets: ${this.packetCount}, Universes: ${Array.from(this.universes).sort((a,b) => a-b).join(',')}`);
          }
        }
      }
    });

    this.socket.on('error', (err) => {
      console.error('Socket error:', err);
    });

    this.socket.bind(6454, '0.0.0.0', () => {
      console.log('Test receiver listening on 0.0.0.0:6454');
    });
  }
}

const receiver = new SimpleArtNetReceiver();
receiver.start();

// Keep running
setInterval(() => {
  console.log(`Status: ${receiver.packetCount} packets from ${receiver.universes.size} universes`);
}, 3000);