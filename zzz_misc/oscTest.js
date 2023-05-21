const OSC = require('osc-js')

const app = new OSC({
    plugin: new OSC.DatagramPlugin({
        port: 7890,
        host: '0.0.0.0',
    })
})

app.on('*', msg => console.log(msg))
app.on('open', () => console.log('Listening'))
app.open({
    port: 7891,
    host: '0.0.0.0',
})