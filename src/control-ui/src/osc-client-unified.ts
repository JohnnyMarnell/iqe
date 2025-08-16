// Simplified OSC client that works with our unified server
export class OscClient {
  private ws: WebSocket | null = null
  private connected = false
  private lastSpeedValue = 0
  private reconnectTimer: any = null

  constructor() {
    this.connect()
  }

  connect() {
    const wsUrl = `ws://${window.location.hostname}:8080`
    console.log(`🔌 Connecting to WebSocket at ${wsUrl}`)
    
    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('🟢 WebSocket Connected')
      this.connected = true
      
      // Clear any reconnect timer
      if (this.reconnectTimer) {
        clearTimeout(this.reconnectTimer)
        this.reconnectTimer = null
      }
      
      // Query current state
      this.queryCurrentState()
    }

    this.ws.onclose = () => {
      console.log('🔴 WebSocket Disconnected')
      this.connected = false
      
      // Try to reconnect after 2 seconds
      this.reconnectTimer = setTimeout(() => {
        console.log('🔄 Attempting to reconnect...')
        this.connect()
      }, 2000)
    }

    this.ws.onerror = (error) => {
      console.error('❌ WebSocket Error:', error)
    }

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data)
        console.log('📥 Received:', msg)
        
        // Handle speed updates
        if (msg.address === '/lx/mixer/master/effect/1/speed') {
          this.lastSpeedValue = msg.args[0]
          window.dispatchEvent(new CustomEvent('speedUpdate', { detail: this.lastSpeedValue }))
        }
      } catch (err) {
        console.error('Error parsing message:', err)
      }
    }
  }

  sendSpeed(value: number) {
    if (!this.connected || !this.ws) {
      console.warn('⚠️ WebSocket not connected, cannot send speed value')
      return
    }
    
    const message = {
      address: '/lx/mixer/master/effect/1/speed',
      args: [value]
    }
    
    console.log('📤 Sending:', message)
    this.ws.send(JSON.stringify(message))
  }

  queryCurrentState() {
    if (!this.connected || !this.ws) {
      console.warn('⚠️ WebSocket not connected, cannot query state')
      return
    }
    
    const message = {
      address: '/lx/osc-query',
      args: [1]
    }
    
    console.log('📤 Querying current state')
    this.ws.send(JSON.stringify(message))
  }
}