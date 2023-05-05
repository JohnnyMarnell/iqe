
let id = 100
const stripLen = 700 // 5 spacing * 140 LED pixels / "numPoints"

console.log(JSON.stringify([
    // 4 rows of 3 pilars, then 3 for rafter cross intersections === 
    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 0   * stripLen, z: 0 + 0 * 3 * stripLen})},
    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 1.5 * stripLen, z: 0 + 0 * 3 * stripLen})},
    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 3   * stripLen, z: 0 + 0 * 3 * stripLen})},

    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 0   * stripLen, z: 0 + 1 * 3 * stripLen})},
    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 1.5 * stripLen, z: 0 + 1 * 3 * stripLen})},
    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 3   * stripLen, z: 0 + 1 * 3 * stripLen})},

    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 0   * stripLen, z: 0 + 2 * 3 * stripLen})},
    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 1.5 * stripLen, z: 0 + 2 * 3 * stripLen})},
    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 3   * stripLen, z: 0 + 2 * 3 * stripLen})},

    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 0   * stripLen, z: 0 + 3 * 3 * stripLen})},
    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 1.5 * stripLen, z: 0 + 3 * 3 * stripLen})},
    {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 3   * stripLen, z: 0 + 3 * 3 * stripLen})},

    // {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 1.5 * stripLen, z: 0 + 0 * 1.5 * stripLen})},
    // {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 1.5 * stripLen, z: 0 + 1 * 1.5 * stripLen})},
    // {...defaultNagBugglerSaberOfLight({roll:90, x: 0 + 1.5 * stripLen, z: 0 + 2 * 1.5 * stripLen})},

    // Ceiling rafters orthogonals, 3 squares of len 3

    // Lastly, rafter cross diagonals ("supply" and "demand")
]))

function defaultNagBugglerSaberOfLight(params) {
    id++
    return {
        id: id,
        class: "org.iqe.NagBugglerLightSaber",
        internal: {
            modulationColor: 0,
            modulationControlsExpanded: true
        },
        parameters: {
            label: "Strip " + id,
            x: 0,
            y: 0,
            z: 0,
            yaw: 0,
            pitch: 0,
            roll: 0,
            scale: 1,
            selected: false,
            deactivate: false,
            enabled: true,
            brightness: 1,
            identify: false,
            mute: false,
            solo: false,
            tags: "strip foo bar",
            protocol: 1,
            byteOrder: 0,
            transport: 0,
            reverse: false,
            host: "192.168.0.10",
            port: 7890,
            dmxChannel: 420,
            artNetUniverse: 1,
            artNetSequenceEnabled: false,
            opcChannel: 0,
            opcOffset: 0,
            ddpDataOffset: 0,
            kinetPort: 1,
            numPoints: 140,
            spacing: 5,
            
            ...params
        },
        children: {}
    }
}