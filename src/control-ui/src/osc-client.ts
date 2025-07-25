import OSC from 'osc-js'

export class OscClient {
  private osc: any
  private connected = false
  private lastSpeedValue = 0

  constructor() {
    this.osc = new OSC({
      plugin: new OSC.WebsocketClientPlugin({ 
        port: 8080, 
        host: window.location.hostname 
      })
    })

    this.osc.on('open', () => {
      console.log('🟢 OSC Connected')
      this.connected = true
    })

    this.osc.on('close', () => {
      console.log('🔴 OSC Disconnected')
      this.connected = false
    })

    // Log all incoming messages
    this.osc.on('*', (msg: any) => {
      console.log('📥 OSC Received:', {
        path: msg.address,
        args: msg.args,
        timestamp: new Date().toISOString()
      })
    })

    this.osc.on('/lx/mixer/master/effect/1/speed', (msg: any) => {
      this.lastSpeedValue = msg.args[0]
      window.dispatchEvent(new CustomEvent('speedUpdate', { detail: this.lastSpeedValue }))
    })
  }

  connect() {
    this.osc.open({ host: window.location.hostname, port: 8080 })
  }

  sendSpeed(value: number) {
    if (!this.connected) {
      console.warn('⚠️ OSC not connected, cannot send speed value')
      return
    }
    
    const path = '/lx/mixer/master/effect/1/speed'
    const msg = new OSC.Message(path, value)
    console.log('📤 OSC Sending:', {
      path: path,
      value: value,
      timestamp: new Date().toISOString()
    })
    this.osc.send(msg)
  }

  queryCurrentState() {
    if (!this.connected) {
      console.warn('⚠️ OSC not connected, cannot query state')
      return
    }
    
    const msg = new OSC.Message('/lx/osc-query', 1)
    console.log('📤 OSC Sending query:', {
      path: '/lx/osc-query',
      timestamp: new Date().toISOString()
    })
    this.osc.send(msg)
  }
}