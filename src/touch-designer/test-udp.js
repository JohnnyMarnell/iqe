const dgram = require('dgram');
const server = dgram.createSocket('udp4');

server.on('error', (err) => {
  console.log(`server error:\n${err.stack}`);
  server.close();
});

server.on('message', (msg, rinfo) => {
  console.log(`server got: ${msg.length} bytes from ${rinfo.address}:${rinfo.port}`);
  // Check if it's ArtNet
  if (msg.length > 8) {
    const header = msg.slice(0, 8).toString('ascii');
    console.log(`Header: "${header}"`);
    if (header.startsWith('Art-Net')) {
      const opcode = msg.readUInt16LE(8);
      const universe = msg.readUInt16LE(14);
      console.log(`ArtNet OpCode: 0x${opcode.toString(16)}, Universe: ${universe}`);
    }
  }
});

server.on('listening', () => {
  const address = server.address();
  console.log(`server listening ${address.address}:${address.port}`);
});

server.bind(6454);

console.log('Test UDP server starting on port 6454...');