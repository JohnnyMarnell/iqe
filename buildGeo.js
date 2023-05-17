const fs = require('fs')

// yaw, pitch, roll, (0,0,0) => along x axis, (0,90,0) => no visual change (so x axis?),
//      (0,0,90) vertical up (y+) (so z axis?)
let id = 100
const stripLen = 700 // 5 spacing * 140 LED pixels / "numPoints"
const s = defaultNagBugglerSaberOfLight
const sl = stripLenMultiplier => stripLenMultiplier * stripLen
const numPillars = 15

function buildNagBugglerSaberOfLightFixtures() {
    return [
        // PILLARS #0 - #14:
        // Going east to west, 4 pillar columns of 3 south to north (x+)
        {...s({roll: -90, x: sl(0  ), z: sl(0 * 3)}, 'pc4 ps4 po6 sq3.4')},
        {...s({roll: -90, x: sl(1.5), z: sl(0 * 3)}, 'pc4 pm7 po5 sq3.3')},
        {...s({roll: -90, x: sl(3  ), z: sl(0 * 3)}, 'pc4 pn4 po4 sq3.2')},

        {...s({roll: -90, x: sl(0  ), z: sl(1 * 3)}, 'pc3 ps3 po7 sq3.5 sq2.4')},
        {...s({roll: -90, x: sl(1.5), z: sl(1 * 3)}, 'pc3 pm5 pi4 sq3.6 sq2.3')},
        {...s({roll: -90, x: sl(3  ), z: sl(1 * 3)}, 'pc3 pn3 po3 sq3.1 sq2.2')},

        {...s({roll: -90, x: sl(0  ), z: sl(2 * 3)}, 'pc2 pc4 ps2 sq2.5 sq1.4 po8')},
        {...s({roll: -90, x: sl(1.5), z: sl(2 * 3)}, 'pc2 pm3 pi2 sq2.6 sq1.3')},
        {...s({roll: -90, x: sl(3  ), z: sl(2 * 3)}, 'pc2 pn2 po2 sq2.1 sq1.2')},

        {...s({roll: -90, x: sl(0  ), z: sl(3 * 3)}, 'pc1 ps1 po9  sq1.5')},
        {...s({roll: -90, x: sl(1.5), z: sl(3 * 3)}, 'pc1 pm1 po10 sq1.6')},
        {...s({roll: -90, x: sl(3  ), z: sl(3 * 3)}, 'pc1 pn1 po1  sq1.1')},

        // then 3 at the rafter diagonal X intersections
        {...s({roll: -90, x: sl(1.5), z: sl((1.5 + 0 * 3))}, 'pm6 pi5 sq3')},
        {...s({roll: -90, x: sl(1.5), z: sl((1.5 + 1 * 3))}, 'pm4 pi3 sq2')},
        {...s({roll: -90, x: sl(1.5), z: sl((1.5 + 2 * 3))}, 'pm2 pi1 sq1')},
    
        // CEILING RAFTERS, #15 - #23:
        // First, 2 rows running along Z+ axis (east to west),
        // each 3 * 3 == 9 strips each, same X+ position
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(1)})},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(2)})},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(3)})},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(4)})},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(5)})},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(6)})},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(7)})},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(8)})},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(9)})}, 

        // #24 - #32
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(1)})},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(2)})},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(3)})},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(4)})},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(5)})},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(6)})},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(7)})},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(8)})},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(9)})},

        // Next, 4 columns running along X-axis, each 3 strips in length
        // #33 - #35
        {...s({yaw: 180, x: sl(1), z: sl(0 * 3)})},
        {...s({yaw: 180, x: sl(2), z: sl(0 * 3)})},
        {...s({yaw: 180, x: sl(3), z: sl(0 * 3)})},
        // #36 - #38
        {...s({yaw: 180, x: sl(1), z: sl(1 * 3)})},
        {...s({yaw: 180, x: sl(2), z: sl(1 * 3)})},
        {...s({yaw: 180, x: sl(3), z: sl(1 * 3)})},
        // #39 - #41
        {...s({yaw: 180, x: sl(1), z: sl(2 * 3)})},
        {...s({yaw: 180, x: sl(2), z: sl(2 * 3)})},
        {...s({yaw: 180, x: sl(3), z: sl(2 * 3)})},
        // #42 - #44
        {...s({yaw: 180, x: sl(1), z: sl(3 * 3)})},
        {...s({yaw: 180, x: sl(2), z: sl(3 * 3)})},
        {...s({yaw: 180, x: sl(3), z: sl(3 * 3)})},
    
        // Lastly, 3 rafter cross diagonals "X"'s, each 2-prong oriented towards center
        //     4 x 2-Prong Order:        /, \ => \/
        //                         \, /,         /\
        // #45 - #48, #49 - #52
        {...s({yaw: -45,  x: 0,                 z: 0  })},
        {...s({yaw: -45,  x: sl(.75),           z: sl(.75)  })},
        {...s({yaw: +45,  x: 0,                 z: sl(3)  })},
        {...s({yaw: +45,  x: sl(.75),           z: sl(3) - sl(.75)  })},
        {...s({yaw: -135, x: sl(3),             z: 0  })},
        {...s({yaw: -135, x: sl(3) - sl(.75),   z: sl(.75)  })},
        {...s({yaw: +135, x: sl(3),             z: sl(3)  })},
        {...s({yaw: +135, x: sl(3) - sl(.75),   z: sl(3) - sl(.75)  })},

        // #53 - #56, #57 - #60
        {...s({yaw: -45,  x: 0,                 z: sl(3)  })},
        {...s({yaw: -45,  x: sl(.75),           z: sl(3) + sl(.75)  })},
        {...s({yaw: +45,  x: 0,                 z: sl(3) + sl(3)  })},
        {...s({yaw: +45,  x: sl(.75),           z: sl(3) + sl(3) - sl(.75)  })},
        {...s({yaw: -135, x: sl(3),             z: sl(3)  })},
        {...s({yaw: -135, x: sl(3) - sl(.75),   z: sl(3) + sl(.75)  })},
        {...s({yaw: +135, x: sl(3),             z: sl(3) + sl(3)  })},
        {...s({yaw: +135, x: sl(3) - sl(.75),   z: sl(3) + sl(3) - sl(.75)  })},

        // #61 - #64, #65 - #68
        {...s({yaw: -45,  x: 0,                 z: sl(6)  })},
        {...s({yaw: -45,  x: sl(.75),           z: sl(6) + sl(.75)  })},
        {...s({yaw: +45,  x: 0,                 z: sl(6) + sl(3)  })},
        {...s({yaw: +45,  x: sl(.75),           z: sl(6) + sl(3) - sl(.75)  })},
        {...s({yaw: -135, x: sl(3),             z: sl(6)  })},
        {...s({yaw: -135, x: sl(3) - sl(.75),   z: sl(6) + sl(.75)  })},
        {...s({yaw: +135, x: sl(3),             z: sl(6) + sl(3)  })},
        {...s({yaw: +135, x: sl(3) - sl(.75),   z: sl(6) + sl(3) - sl(.75)  })},
    ]
}

// Load project file, overwrite fixtures, re-write file.
const path = `${__dirname}/iqe.lxp`
const project = JSON.parse(fs.readFileSync(path))
project.model.fixtures = buildNagBugglerSaberOfLightFixtures()
console.log(JSON.stringify(project, null, 2))
fs.writeFileSync(path, JSON.stringify(project, null, 2))

function defaultNagBugglerSaberOfLight(params, tags) {
    id++
    let fixtureTags = `strip ${id - 100 <= numPillars ? 'pillar' : 'rafter'} f${id - 101}`
    if (tags) fixtureTags += ' ' + tags.split(/\s+/ig).join(' ')
    return {
        id: id,
        class: "org.iqe.NagBugglerSaberOfLightFixture",
        internal: {
            modulationColor: 0,
            modulationControlsExpanded: true
        },
        parameters: {
            label: (id - 100 <= numPillars ? `Pillar ${id - 100}` : `Rafter ${id - 100 - numPillars}`) + '; #' + (id - 101),
            tags: fixtureTags,
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