const fs = require('fs')

// yaw, pitch, roll, (0,0,0) => along x axis, (0,90,0) => no visual change (so x axis?),
//      (0,0,90) vertical up (y+) (so z axis?)
let id = 100
const stripLen = 700 // 5 spacing * 140 LED pixels / "numPoints"
const s = defaultNagBugglerSaberOfLight
const numPillars = 15

function buildNagBugglerSaberOfLightFixtures() {
    return [
        // PILLARS #0 - #14:
        // 4 rows of 3 pillars, then 3 for rafter cross intersections ===
        {...s({roll: -90, x: 0 + 0   * stripLen, z: 0 + 0 * 3 * stripLen})},
        {...s({roll: -90, x: 0 + 1.5 * stripLen, z: 0 + 0 * 3 * stripLen})},
        {...s({roll: -90, x: 0 + 3   * stripLen, z: 0 + 0 * 3 * stripLen})},

        {...s({roll: -90, x: 0 + 0   * stripLen, z: 0 + 1 * 3 * stripLen})},
        {...s({roll: -90, x: 0 + 1.5 * stripLen, z: 0 + 1 * 3 * stripLen})},
        {...s({roll: -90, x: 0 + 3   * stripLen, z: 0 + 1 * 3 * stripLen})},

        {...s({roll: -90, x: 0 + 0   * stripLen, z: 0 + 2 * 3 * stripLen})},
        {...s({roll: -90, x: 0 + 1.5 * stripLen, z: 0 + 2 * 3 * stripLen})},
        {...s({roll: -90, x: 0 + 3   * stripLen, z: 0 + 2 * 3 * stripLen})},

        {...s({roll: -90, x: 0 + 0   * stripLen, z: 0 + 3 * 3 * stripLen})},
        {...s({roll: -90, x: 0 + 1.5 * stripLen, z: 0 + 3 * 3 * stripLen})},
        {...s({roll: -90, x: 0 + 3   * stripLen, z: 0 + 3 * 3 * stripLen})},

        {...s({roll: -90, x: 0 + 1.5 * stripLen, z: (1.5 + 0 * 3) * stripLen})},
        {...s({roll: -90, x: 0 + 1.5 * stripLen, z: (1.5 + 1 * 3) * stripLen})},
        {...s({roll: -90, x: 0 + 1.5 * stripLen, z: (1.5 + 2 * 3) * stripLen})},
    
        // CEILING RAFTERS, #15 - #23:
        // First, 2 rows running along Z-axis, each 3 * 3 == 9 strips each, same + x dir
        {...s({yaw: 90, x: 0 + 0 * 1.5 * stripLen, z: 0 + 1 * stripLen})},
        {...s({yaw: 90, x: 0 + 0 * 1.5 * stripLen, z: 0 + 2 * stripLen})},
        {...s({yaw: 90, x: 0 + 0 * 1.5 * stripLen, z: 0 + 3 * stripLen})},
        {...s({yaw: 90, x: 0 + 0 * 1.5 * stripLen, z: 0 + 4 * stripLen})},
        {...s({yaw: 90, x: 0 + 0 * 1.5 * stripLen, z: 0 + 5 * stripLen})},
        {...s({yaw: 90, x: 0 + 0 * 1.5 * stripLen, z: 0 + 6 * stripLen})},
        {...s({yaw: 90, x: 0 + 0 * 1.5 * stripLen, z: 0 + 7 * stripLen})},
        {...s({yaw: 90, x: 0 + 0 * 1.5 * stripLen, z: 0 + 8 * stripLen})},
        {...s({yaw: 90, x: 0 + 0 * 1.5 * stripLen, z: 0 + 9 * stripLen})}, 

        // #24 - #32
        {...s({yaw: 90, x: 0 + 2 * 1.5 * stripLen, z: 0 + 1 * stripLen})},
        {...s({yaw: 90, x: 0 + 2 * 1.5 * stripLen, z: 0 + 2 * stripLen})},
        {...s({yaw: 90, x: 0 + 2 * 1.5 * stripLen, z: 0 + 3 * stripLen})},
        {...s({yaw: 90, x: 0 + 2 * 1.5 * stripLen, z: 0 + 4 * stripLen})},
        {...s({yaw: 90, x: 0 + 2 * 1.5 * stripLen, z: 0 + 5 * stripLen})},
        {...s({yaw: 90, x: 0 + 2 * 1.5 * stripLen, z: 0 + 6 * stripLen})},
        {...s({yaw: 90, x: 0 + 2 * 1.5 * stripLen, z: 0 + 7 * stripLen})},
        {...s({yaw: 90, x: 0 + 2 * 1.5 * stripLen, z: 0 + 8 * stripLen})},
        {...s({yaw: 90, x: 0 + 2 * 1.5 * stripLen, z: 0 + 9 * stripLen})},

        // Next, 4 columns running along X-axis, each 3 strips in length
        // #33 - #35
        {...s({yaw: 180, x: 0 + 1 * stripLen, z: 0 + 0 * 3 * stripLen})},
        {...s({yaw: 180, x: 0 + 2 * stripLen, z: 0 + 0 * 3 * stripLen})},
        {...s({yaw: 180, x: 0 + 3 * stripLen, z: 0 + 0 * 3 * stripLen})},
        // #36 - #38
        {...s({yaw: 180, x: 0 + 1 * stripLen, z: 0 + 1 * 3 * stripLen})},
        {...s({yaw: 180, x: 0 + 2 * stripLen, z: 0 + 1 * 3 * stripLen})},
        {...s({yaw: 180, x: 0 + 3 * stripLen, z: 0 + 1 * 3 * stripLen})},
        // #39 - #41
        {...s({yaw: 180, x: 0 + 1 * stripLen, z: 0 + 2 * 3 * stripLen})},
        {...s({yaw: 180, x: 0 + 2 * stripLen, z: 0 + 2 * 3 * stripLen})},
        {...s({yaw: 180, x: 0 + 3 * stripLen, z: 0 + 2 * 3 * stripLen})},
        // #42 - #44
        {...s({yaw: 180, x: 0 + 1 * stripLen, z: 0 + 3 * 3 * stripLen})},
        {...s({yaw: 180, x: 0 + 2 * stripLen, z: 0 + 3 * 3 * stripLen})},
        {...s({yaw: 180, x: 0 + 3 * stripLen, z: 0 + 3 * 3 * stripLen})},
    
        // Lastly, 3 rafter cross diagonals "X"'s, each 2-prong oriented towards center
        //     2 Prong Order:        /, \ => \/
        //                     \, /,         /\
        // #45 - #48, #49 - #52
        {...s({yaw: -45,  x: 0,                                 z: 0  })},
        {...s({yaw: -45,  x: 0 + .75 * stripLen,                z: 0 + .75 * stripLen  })},
        {...s({yaw: +45,  x: 0,                                 z: 0 + 3 * stripLen  })},
        {...s({yaw: +45,  x: 0 + .75 * stripLen,                z: 0 + 3 * stripLen - .75 * stripLen  })},
        {...s({yaw: -135, x: 0 + 3 * stripLen,                  z: 0  })},
        {...s({yaw: -135, x: 0 + 3 * stripLen - .75 * stripLen, z: 0 + .75 * stripLen  })},
        {...s({yaw: +135, x: 0 + 3 * stripLen,                  z: 0 + 3 * stripLen  })},
        {...s({yaw: +135, x: 0 + 3 * stripLen - .75 * stripLen, z: 0 + 3 * stripLen - .75 * stripLen  })},

        // #53 - #56, #57 - #60
        {...s({yaw: -45,  x: 0,                                 z: 3 * stripLen  })},
        {...s({yaw: -45,  x: 0 + .75 * stripLen,                z: 3 * stripLen + .75 * stripLen  })},
        {...s({yaw: +45,  x: 0,                                 z: 3 * stripLen + 3 * stripLen  })},
        {...s({yaw: +45,  x: 0 + .75 * stripLen,                z: 3 * stripLen + 3 * stripLen - .75 * stripLen  })},
        {...s({yaw: -135, x: 0 + 3 * stripLen,                  z: 3 * stripLen  })},
        {...s({yaw: -135, x: 0 + 3 * stripLen - .75 * stripLen, z: 3 * stripLen + .75 * stripLen  })},
        {...s({yaw: +135, x: 0 + 3 * stripLen,                  z: 3 * stripLen + 3 * stripLen  })},
        {...s({yaw: +135, x: 0 + 3 * stripLen - .75 * stripLen, z: 3 * stripLen + 3 * stripLen - .75 * stripLen  })},

        // #61 - #64, #65 - #68
        {...s({yaw: -45,  x: 0,                                 z: 6 * stripLen  })},
        {...s({yaw: -45,  x: 0 + .75 * stripLen,                z: 6 * stripLen + .75 * stripLen  })},
        {...s({yaw: +45,  x: 0,                                 z: 6 * stripLen + 3 * stripLen  })},
        {...s({yaw: +45,  x: 0 + .75 * stripLen,                z: 6 * stripLen + 3 * stripLen - .75 * stripLen  })},
        {...s({yaw: -135, x: 0 + 3 * stripLen,                  z: 6 * stripLen  })},
        {...s({yaw: -135, x: 0 + 3 * stripLen - .75 * stripLen, z: 6 * stripLen + .75 * stripLen  })},
        {...s({yaw: +135, x: 0 + 3 * stripLen,                  z: 6 * stripLen + 3 * stripLen  })},
        {...s({yaw: +135, x: 0 + 3 * stripLen - .75 * stripLen, z: 6 * stripLen + 3 * stripLen - .75 * stripLen  })},
    ]
}

// Load project file, overwrite fixtures, re-write file.
const path = `${__dirname}/iqe.lxp`
const project = JSON.parse(fs.readFileSync(path))
project.model.fixtures = buildNagBugglerSaberOfLightFixtures()
console.log(JSON.stringify(project, null, 2))
fs.writeFileSync(path, JSON.stringify(project, null, 2))

function defaultNagBugglerSaberOfLight(params) {
    id++
    return {
        id: id,
        class: "org.iqe.NagBugglerSaberOfLight",
        internal: {
            modulationColor: 0,
            modulationControlsExpanded: true
        },
        parameters: {
            label: (id - 100 <= numPillars ? `Pillar ${id - 100}` : `Rafter ${id - 100 - numPillars}`) + '; #' + (id - 101),
            tags: `strip ${id - 100 <= numPillars ? 'pillar' : 'rafter'} f${id - 101}`,
            x: 0,
            y: stripLen, // most (all) strips have origin in ceiling
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
            
            // overlay any overriding params from above!
            ...params
        },
        children: {}
    }
}