const OSC = require('osc-js')
const express = require('express')
const {MidiIn, MidiOut, Midi} = require('j5-midi')

function bridge(webPort = 80, wsPort = 8080, appTo = 3030, appFrom = 3131, exclude = null) {
    // Open port for receiving OSC messages from APP
    if (exclude) exclude = new RegExp(exclude, "gi")
    const last = {}
    const app = new OSC({plugin: new OSC.DatagramPlugin({ port: appFrom, send: { port: appTo } })})
    app.on('open', () => {
        console.log('OSC listening from server, excluding logs that match regEx:', exclude)
        console.log('Started with these options def (osc js lib used is cryptic, idk if all are correct/used):')
        console.log(app.options.plugin.options)
    })
    app.on('*', msg => last[msg.address] = msg)
    app.on('*', msg => (!exclude || !msg.address.match(exclude)) && console.log('APP', msg.address, ...msg.args))
    app.open({ port: appFrom })

    // Open a websocket bridge, for web app send and receive bridging; wire to/from APP
    const oscBridge = new OSC({ plugin: new OSC.WebsocketServerPlugin({ port: wsPort, host: '0.0.0.0' }) })
    oscBridge.on('open', () => console.log('Bridge listening', oscBridge.options.plugin.options))
    oscBridge.on('*', msg => app.send(new OSC.Message(msg.address, ...msg.args)))
    app.on('*', msg => oscBridge.send(new OSC.Message(msg.address, ...msg.args)))
    oscBridge.on('*', msg => console.log('WSC', msg.address, ...msg.args))
    oscBridge.open()

    // Start a webserver to serve the app
    const expressApp = express()
    expressApp.use('/', express.static('./dist'))
    expressApp.use('/state', (req, res) => res.json(last))
    expressApp.listen(webPort, () => console.log('Web server listening on port', webPort))

    wireMidi(app)
}

function wireMidi(app) {
    const mac = require('os').platform() === 'darwin'
    const out = new MidiOut({pattern: mac ? /IAC/ig : /Thru/ig })
    const input = mac ? new MidiIn({pattern: 'Launchkey Mini MK3 MIDI Port', virtual: true}) :
        // new MidiIn({pattern: /Launchkey.*(MIDI 1|MIDI Port$)/ig}) // todo
        new MidiIn({pattern: /Launchkey/ig}) // todo
    input.on('midi.note', msg => {
        const oscMsg = new OSC.Message('/iqe/midi', msg.type, msg.data, msg.value)
        app.send(oscMsg)
        console.log(oscMsg.address, ...oscMsg.args)
    })
    input.on('midi.cc', msg => {
        msg.value = 64 + Math.floor(msg.value / 128 * 12)
        Midi.setChannel(msg, 15)
        out.send(msg)
    })
}

function bridgeSend(path, data) {
    console.log('test', path, data)
    const osc = new OSC({ plugin: new OSC.WebsocketClientPlugin({ port: wsPort, host: '0.0.0.0' })})
    data = JSON.parse(data)
    if (!data.length) data = [ data ]    
    osc.on('open', () => { osc.send(new OSC.Message(path, ...data)) ; osc.close() })
    osc.open()
}

const args = process.argv.join(' ').toLowerCase()
const eargs = (key, defaultVal) => (key = `IQE_${key}`) && key in process.env ? process.env[key] : defaultVal
const eargi = (key, defaultVal) => parseInt(eargs(key, defaultVal))

const [webPort, wsPort, appTo, appFrom] = [eargi('WEB_PORT', 80), eargi('OSC_WS_PORT', 8080), eargi('APP_OSC_TO_PORT', 3030),
    eargi('APP_OSC_FROM_PORT', 3131)], exclude = eargs('EXCLUDE', null)
if (args.includes('bridge'))
    bridge(webPort, wsPort, appTo, appFrom, exclude)
else if (args.includes('send'))
    bridgeSend(...process.argv.slice(3))
