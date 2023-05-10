const OSC = require('osc-js')
const express = require('express')

function bridge(webPort = 80, wsPort = 8080, lxTo = 3030, lxFrom = 3131) {
    // Open port for receiving OSC messages from LX
    const last = {}
    const lx = new OSC({plugin: new OSC.DatagramPlugin({ port: lxFrom, send: { port: lxTo } })})
    lx.on('open', () => console.log('LX OSC echo listening on port', lxFrom))
    lx.on('*', msg => last[msg.address] = msg)
    lx.on('*', msg => !msg.address.startsWith('/lx/palette/swatch/color')
                       && console.log(msg.address, ...msg.args))
    lx.open({ port: lxFrom })

    // Open a websocket bridge, for web app send and receive bridging; wire to/from LX
    const oscBridge = new OSC({ plugin: new OSC.WebsocketServerPlugin({ port: wsPort, host: '0.0.0.0' }) })
    oscBridge.on('open', () => console.log('Bridge listening', oscBridge.options.plugin.options))
    oscBridge.on('*', msg => lx.send(new OSC.Message(msg.address, ...msg.args)))
    lx.on('*', msg => oscBridge.send(new OSC.Message(msg.address, ...msg.args)))
    oscBridge.open()

    // Start a webserver to serve the app
    const app = express()
    app.use('/', express.static('./dist'))
    app.use('/state', (req, res) => res.json(last))
    app.listen(webPort, () => console.log('Web server listening on port', webPort))
}

function bridgeSend(path, data) {
    const osc = new OSC()
    data = JSON.parse(data)
    if (!data.length) data = [ data ]    
    osc.on('open', () => osc.send(new OSC.Message(path, ...data)))
    osc.open()
}

const args = process.argv.join(' ').toLowerCase()
const earg = (key, defaultVal) => parseInt(process.env[`IQE_${key}`] || defaultVal)

if (args.includes('bridge'))
    bridge(earg('WEB_PORT', 80), earg('OSC_WS_PORT', 8080), earg('LX_OSC_TO_PORT', 3030),
           earg('LX_OSC_FROM_PORT', 3131))
else if (args.includes('send'))
    bridgeSend(...process.argv.slice(3))
