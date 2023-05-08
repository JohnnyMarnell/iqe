const OSC = require('osc-js')

function bridge(port = 8080, lxTo = 3030, lxFrom = 3131) {
    const lxRecv = new OSC({plugin: new OSC.DatagramPlugin({ port: lxFrom })})
    lxRecv.on('open', () => console.log('LX OSC echo listening on port', lxFrom))
    lxRecv.on('*', msg => console.log(JSON.stringify(msg)))
    lxRecv.open({ port: lxFrom })

    const bridgeConfig = { wsServer: { port: port }, udpClient: { port: lxTo } }
    const oscBridge = new OSC({plugin: new OSC.BridgePlugin(bridgeConfig)})
    oscBridge.on('open', () => console.log('Bridge listening', oscBridge.options.plugin.options))
    oscBridge.on('*', msg => console.log(msg))
    oscBridge.open()
}

function bridgeSend(path, data) {
    const osc = new OSC()
    data = JSON.parse(data)
    if (!data.length) data = [ data ]    
    osc.on('open', () => osc.send(new OSC.Message(path, ...data)))
    osc.open()
}

const args = process.argv.join(' ').toLowerCase()
console.log(args, args.includes('send'))
if (args.includes('bridge'))
    bridge()
else if (args.includes('send'))
    bridgeSend(...process.argv.slice(3))
    