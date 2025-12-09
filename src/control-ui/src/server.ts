const express = require('express')
const { createServer } = require('http')
const { WebSocketServer } = require('ws')
const path = require('path')
const fs = require('fs')
const OSC = require('osc-js')
const os = require('os')

// Configuration
const WEB_PORT = 8282
const WS_PORT = 8080
const LX_OSC_PORT = 3232
const LX_OSC_LISTEN_PORT = 3333
const LX_HOST = 'localhost'

class UnifiedServer {
  private app: any
  private oscBridge: any
  private oscToLX: any
  private wsServer: any
  private wsClients: Set<any> = new Set()

  constructor() {
    this.app = express()
    this.setupOSCBridge()

    // Only start HTTP server in production (check for dist AND specific env var)
    if (process.env.NODE_ENV === 'production' || process.argv.includes('--production')) {
      this.setupWebServer()
    } else {
      console.log('📦 Running in DEV mode - Vite handles web serving on port 8282')
      console.log('📦 This server provides OSC/WebSocket bridge only')
    }
  }

  private setupWebServer() {
    // Serve static files from dist directory (after build)
    const distPath = path.join(__dirname, '..', 'dist')

    // Production mode - serve static files
    this.app.use(express.static(distPath))

    // Serve index.html for all routes (SPA support)
    this.app.get('*', (req: any, res: any) => {
      res.sendFile(path.join(distPath, 'index.html'))
    })

    // Start web server (production mode only)
    const server = createServer(this.app)
    server.listen(WEB_PORT, () => {
      console.log(`🌐 Web UI server running on http://localhost:${WEB_PORT}`)
    })
  }

  private setupOSCBridge() {
    // Create WebSocket server for browser clients
    this.wsServer = new WebSocketServer({ port: WS_PORT })
    console.log(`📡 WebSocket server running on port ${WS_PORT}`)

    // Setup OSC UDP connection to LX
    this.oscToLX = new OSC({
      plugin: new OSC.DatagramPlugin({
        send: {
          host: LX_HOST,
          port: LX_OSC_PORT
        },
        open: {
          host: '0.0.0.0',
          port: LX_OSC_LISTEN_PORT
        }
      })
    })

    // Handle WebSocket connections
    this.wsServer.on('connection', (ws: any) => {
      console.log('🔌 New WebSocket client connected')
      this.wsClients.add(ws)

      ws.on('message', (data: Buffer) => {
        try {
          const message = JSON.parse(data.toString())
          
          // Handle OSC messages from web client
          if (message.address) {
            const oscMsg = new OSC.Message(message.address, ...(message.args || []))
            this.oscToLX.send(oscMsg)
            console.log('📤 Forwarding to LX:', message.address, message.args)
          }
        } catch (err) {
          console.error('Error processing WebSocket message:', err)
        }
      })

      ws.on('close', () => {
        console.log('🔌 WebSocket client disconnected')
        this.wsClients.delete(ws)
      })

      ws.on('error', (err: Error) => {
        console.error('WebSocket error:', err)
        this.wsClients.delete(ws)
      })
    })

    // Handle OSC messages from LX
    this.oscToLX.on('*', (msg: any) => {
      const message = {
        address: msg.address,
        args: msg.args,
        timestamp: new Date().toISOString()
      }
      
      // Forward to all connected WebSocket clients
      const messageStr = JSON.stringify(message)
      this.wsClients.forEach(client => {
        if (client.readyState === 1) { // WebSocket.OPEN
          client.send(messageStr)
        }
      })
      
      console.log('📥 From LX:', msg.address, msg.args)
    })

    // Open OSC connection
    this.oscToLX.open()
    console.log(`🎮 OSC bridge connected to LX on port ${LX_OSC_PORT}`)
    console.log(`👂 Listening for OSC from LX on port ${LX_OSC_LISTEN_PORT}`)
  }

  start() {
    console.log('\n✨ Unified Speed Control Server Started!')
    console.log('━'.repeat(50))
    console.log(`📱 Open http://localhost:${WEB_PORT} in your browser`)
    console.log(`   Or http://${os.hostname()}:${WEB_PORT} from another device`)
    console.log('━'.repeat(50))
    console.log('⚠️  Make sure LX/Chromatik is running with OSC enabled')
    console.log('Press Ctrl+C to stop\n')
  }
}

// Start the server
const server = new UnifiedServer()
server.start()