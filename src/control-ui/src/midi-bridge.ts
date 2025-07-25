import { WebMidi, Input } from 'webmidi'
import OSC from 'osc-js'

// MIDI to OSC bridge configuration
const MIDI_CC_SPEED = 21
const OSC_SPEED_PATH = '/lx/mixer/master/effect/1/speed'
const OSC_PORT = 3232  // Send to LX OSC receiver port

// Create OSC client
const osc = new OSC({ 
  plugin: new OSC.DatagramPlugin({ 
    send: { port: OSC_PORT, host: 'localhost' } 
  }) 
})

console.log('🎹 MIDI Bridge Starting...')

// Enable WebMidi
WebMidi
  .enable()
  .then(() => {
    console.log('✅ WebMidi enabled!')
    
    // Filter out IAC devices and sort by preference
    const validInputs = WebMidi.inputs.filter((input: Input) => {
      const nameLower = input.name.toLowerCase()
      return !nameLower.includes('iac')
    })
    
    // Sort devices: prioritize "daw" first, then "key"
    const sortedInputs = validInputs.sort((a: Input, b: Input) => {
      const aName = a.name.toLowerCase()
      const bName = b.name.toLowerCase()
      
      // DAW devices get highest priority
      const aDaw = aName.includes('daw')
      const bDaw = bName.includes('daw')
      if (aDaw && !bDaw) return 1
      if (!aDaw && bDaw) return -1
      
      // Key devices get second priority
      const aKey = aName.includes('key')
      const bKey = bName.includes('key')
      if (aKey && !bKey) return -1
      if (!aKey && bKey) return 1
      
      // Otherwise alphabetical
      return aName.localeCompare(bName)
    })
    
    // List available MIDI inputs
    console.log('Available MIDI inputs (filtered, sorted):')
    sortedInputs.forEach((input: Input, index: number) => {
      console.log(`  ${index}: ${input.name} (${input.id})`)
    })
    
    if (sortedInputs.length === 0) {
      console.error('❌ No valid MIDI devices found! (IAC devices excluded)')
      return
    }
    
    // Connect to best MIDI input
    const midiInput = sortedInputs[0]
    console.log(`📡 Connecting to: ${midiInput.name}`)
    console.log(`   Bridging CC ${MIDI_CC_SPEED} → ${OSC_SPEED_PATH}`)
    
    // Listen for control change messages on all channels
    midiInput.addListener('controlchange', (e) => {
      const channel = e.message.channel
      const controller = e.controller.number
      const value = e.value  // 0 to 1?
      
      console.log(`📥 MIDI CC: Channel ${channel}, CC ${controller}, Value ${value}`)
      
      // Handle speed control
      if (controller === MIDI_CC_SPEED) {
        const oscValue = value
        
        console.log(`🎚️  Speed CC ${MIDI_CC_SPEED}: ${value} → OSC ${oscValue.toFixed(3)}`)
        
        // Send OSC message
        const msg = new OSC.Message(OSC_SPEED_PATH, oscValue)
        osc.send(msg)
        console.log(`📤 OSC Sent: ${OSC_SPEED_PATH} ${oscValue.toFixed(3)}`)
      }
    })
    
    // Open OSC connection
    osc.open()
    console.log(`🌐 OSC client ready, sending to localhost:${OSC_PORT}`)
    console.log('🎛️  MIDI bridge running. Press Ctrl+C to stop.')
    console.log(`   Move CC ${MIDI_CC_SPEED} on your MIDI controller to control speed.`)
  })
  .catch((err: Error) => {
    console.error('❌ Error enabling WebMidi:', err)
  })

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('\n👋 Closing MIDI bridge...')
  WebMidi.disable()
  osc.close()
  process.exit()
})