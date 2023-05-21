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
        /* 
            Tags for membership (shapes/outlines/sets), and directional order progression therein
                (e.g. clockwise [first, 1, starts upper left / northwest corner], east, south,
                 diagonals moving southeast and northwest, etc)
            pc, po, pi, ps, pn, pm: pillar columns (running N to S), outer, inner, rows (W to E) south, north, middle
            e.g. pc4-s2 means the second pillar progressing southward through 4th pillar column
            Per the data/power diagrams, West to East progression in general increases numerically (e.g. squares 1 - 3)

            PILLARS #0 - #14:
            Going east to west, 4 pillar columns of 3 south to north (x+)
        */
        {...s({roll: -90, x: sl(0  ), z: sl(0 * 3)}, 'pc4 pc4-s3 ps ps-e4 po po-cw6 sq3 sq3-cw4')},
        {...s({roll: -90, x: sl(1.5), z: sl(0 * 3)}, 'pc4 pc4-s2 pm pm-e7 po po-cw5 sq3 sq3-cw3')},
        {...s({roll: -90, x: sl(3  ), z: sl(0 * 3)}, 'pc4 pc4-s1 pn pn-e4 po po-cw4 sq3 sq3-cw2')},

        {...s({roll: -90, x: sl(0  ), z: sl(1 * 3)}, 'pc3 pc3-s3 ps ps-e3 po po-cw7 sq3 sq3-cw5 sq2 sq2-cw4')},
        {...s({roll: -90, x: sl(1.5), z: sl(1 * 3)}, 'pc3 pc3-s2 pm pm-e5 pi pi-e4  sq3 sq3-cw6 sq2 sq2-cw3')},
        {...s({roll: -90, x: sl(3  ), z: sl(1 * 3)}, 'pc3 pc3-s1 pn pn-e3 po po-cw3 sq3 sq3-cw1 sq2 sq2-cw2')},

        {...s({roll: -90, x: sl(0  ), z: sl(2 * 3)}, 'pc2 pc2-s3 ps ps-e4 po po-cw8 sq2 sq2-cw5 sq1 sq1-cw4')},
        {...s({roll: -90, x: sl(1.5), z: sl(2 * 3)}, 'pc2 pc2-s2 pm pm-e3 pi pi-e2  sq2 sq2-cw6 sq1 sq1-cw3')},
        {...s({roll: -90, x: sl(3  ), z: sl(2 * 3)}, 'pc2 pc2-s1 pn pn-e2 po po-cw2 sq2 sq2-cw1 sq1 sq1-cw2')},

        {...s({roll: -90, x: sl(0  ), z: sl(3 * 3)}, 'pc1 pc1-s3 ps ps-e1 po po-cw9  sq1 sq1-cw5')},
        {...s({roll: -90, x: sl(1.5), z: sl(3 * 3)}, 'pc1 pc1-s2 pm pm-e1 po po-cw10 sq1 sq1-cw6')},
        {...s({roll: -90, x: sl(3  ), z: sl(3 * 3)}, 'pc1 pc1-s1 pn pn-e1 po po-cw1  sq1 sq1-cw1')},

        // then 3 at the rafter diagonal X intersections
        {...s({roll: -90, x: sl(1.5), z: sl((1.5 + 0 * 3))}, 'pm pm-e6 pi pi-e5 sq3')},
        {...s({roll: -90, x: sl(1.5), z: sl((1.5 + 1 * 3))}, 'pm pm-e4 pi pi-e3 sq2')},
        {...s({roll: -90, x: sl(1.5), z: sl((1.5 + 2 * 3))}, 'pm pm-e2 pi pi-e1 sq1')},
    
        // CEILING RAFTERS, #15 - #23:
        // First, 2 rows running along Z+ axis (progressing and facing east to west),
        // each 3 * 3 == 9 strips each, same X+ position
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(1)}, 'rn-e9 ro-cw9 sq3 sq3-cw3')},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(2)}, 'rn-e8 ro-cw8 sq3 sq3-cw2')},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(3)}, 'rn-e7 ro-cw7 sq3 sq3-cw1')},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(4)}, 'rn-e6 ro-cw6 sq2 sq2-cw3')},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(5)}, 'rn-e5 ro-cw5 sq2 sq2-cw2')},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(6)}, 'rn-e4 ro-cw4 sq2 sq2-cw1')},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(7)}, 'rn-e3 ro-cw3 sq1 sq1-cw3')},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(8)}, 'rn-e2 ro-cw2 sq1 sq1-cw2')},
        {...s({yaw: 90, x: sl(0 * 1.5), z: sl(9)}, 'rn-e1 ro-cw1 sq1 sq1-cw1')},

        // #24 - #32
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(1)}, 'rs-e9 ro-cw13 sq3 sq3-cw7')},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(2)}, 'rs-e8 ro-cw14 sq3 sq3-cw8')},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(3)}, 'rs-e7 ro-cw15 sq3 sq3-cw9')},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(4)}, 'rs-e6 ro-cw16 sq2 sq2-cw7')},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(5)}, 'rs-e5 ro-cw17 sq2 sq2-cw8')},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(6)}, 'rs-e4 ro-cw18 sq2 sq2-cw9')},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(7)}, 'rs-e3 ro-cw19 sq1 sq1-cw7')},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(8)}, 'rs-e2 ro-cw20 sq1 sq1-cw8')},
        {...s({yaw: 90, x: sl(2 * 1.5), z: sl(9)}, 'rs-e1 ro-cw21 sq1 sq1-cw9')},

        // Next, 4 columns running along X-axis, each 3 strips in length
        // #33 - #35
        {...s({yaw: 180, x: sl(1), z: sl(0 * 3)}, 'rc4 rc4-s3 sq3 sq3-cw6')},
        {...s({yaw: 180, x: sl(2), z: sl(0 * 3)}, 'rc4 rc4-s2 sq3 sq3-cw5')},
        {...s({yaw: 180, x: sl(3), z: sl(0 * 3)}, 'rc4 rc4-s1 sq3 sq3-cw4')},
        // #36 - #38
        {...s({yaw: 180, x: sl(1), z: sl(1 * 3)}, 'rc3 rc1-s3 sq2 sq2-cw6 sq3 sq3-cw10')},
        {...s({yaw: 180, x: sl(2), z: sl(1 * 3)}, 'rc3 rc1-s2 sq2 sq2-cw5 sq3 sq3-cw11')},
        {...s({yaw: 180, x: sl(3), z: sl(1 * 3)}, 'rc3 rc1-s1 sq2 sq2-cw4 sq3 sq3-cw12')},
        // #39 - #41
        {...s({yaw: 180, x: sl(1), z: sl(2 * 3)}, 'rc2 rc1-s3 sq1 sq1-cw6 sq2 sq2-cw10')},
        {...s({yaw: 180, x: sl(2), z: sl(2 * 3)}, 'rc2 rc1-s2 sq1 sq1-cw5 sq2 sq2-cw11')},
        {...s({yaw: 180, x: sl(3), z: sl(2 * 3)}, 'rc2 rc1-s1 sq1 sq1-cw4 sq2 sq2-cw12')},
        // #42 - #44
        {...s({yaw: 180, x: sl(1), z: sl(3 * 3)}, 'rc1 rc1-s3 sq1 sq1-cw10')},
        {...s({yaw: 180, x: sl(2), z: sl(3 * 3)}, 'rc1 rc1-s2 sq1 sq1-cw11')},
        {...s({yaw: 180, x: sl(3), z: sl(3 * 3)}, 'rc1 rc1-s1 sq1 sq1-cw12')},
    
        // Lastly, 3 rafter cross diagonals "X"'s, each quarter (2-strip prong) is oriented towards center
        //     Per 3 squares, 8 strip "X" / cross order of geometry specificying below:
        //
        //                 /,    \,           \  /
        //                    /,    \    =>    \/
        //        \,    /,               =>    /\
        //     \,    /,                       /  \
        // 
        // #45 - #48, #49 - #52
        {...s({yaw: -45,  x: 0,                 z: 0  },                        'x3-3 sq3 sq3-se4 x xo xo-cw3')},
        {...s({yaw: -45,  x: sl(.75),           z: sl(.75)  },                  'x3-3 sq3 sq3-se3 x xi xi-cw3')},
        {...s({yaw: +45,  x: 0,                 z: sl(3)  },                    'x4-3 sq3 sq3-nw1 x xo xo-cw4')},
        {...s({yaw: +45,  x: sl(.75),           z: sl(3) - sl(.75)  },          'x4-3 sq3 sq3-nw2 x xi xi-cw4')},
        {...s({yaw: -135, x: sl(3),             z: 0  },                        'x2-3 sq3 sq3-nw4 x xo xo-cw2')},
        {...s({yaw: -135, x: sl(3) - sl(.75),   z: sl(.75)  },                  'x2-3 sq3 sq3-nw3 x xi xi-cw2')},
        {...s({yaw: +135, x: sl(3),             z: sl(3)  },                    'x1-3 sq3 sq3-se1 x xo xo-cw1')},
        {...s({yaw: +135, x: sl(3) - sl(.75),   z: sl(3) - sl(.75)  },          'x1-3 sq3 sq3-se2 x xi xi-cw1')},

        // #53 - #56, #57 - #60
        {...s({yaw: -45,  x: 0,                 z: sl(3)  },                    'x3-2 sq2 sq2-se4 x xo xo-cw3')},
        {...s({yaw: -45,  x: sl(.75),           z: sl(3) + sl(.75)  },          'x3-2 sq2 sq2-se3 x xi xi-cw3')},
        {...s({yaw: +45,  x: 0,                 z: sl(3) + sl(3)  },            'x4-2 sq2 sq2-nw1 x xo xo-cw4')},
        {...s({yaw: +45,  x: sl(.75),           z: sl(3) + sl(3) - sl(.75)  },  'x4-2 sq2 sq2-nw2 x xi xi-cw4')},
        {...s({yaw: -135, x: sl(3),             z: sl(3)  },                    'x2-2 sq2 sq2-nw4 x xo xo-cw2')},
        {...s({yaw: -135, x: sl(3) - sl(.75),   z: sl(3) + sl(.75)  },          'x2-2 sq2 sq2-nw3 x xi xi-cw2')},
        {...s({yaw: +135, x: sl(3),             z: sl(3) + sl(3)  },            'x1-2 sq2 sq2-se1 x xo xo-cw1')},
        {...s({yaw: +135, x: sl(3) - sl(.75),   z: sl(3) + sl(3) - sl(.75)  },  'x1-2 sq2 sq2-se2 x xi xi-cw1')},

        // #61 - #64, #65 - #68
        {...s({yaw: -45,  x: 0,                 z: sl(6)  },                    'x3-1 sq1 sq1-se4 x xo xo-cw3')},
        {...s({yaw: -45,  x: sl(.75),           z: sl(6) + sl(.75)  },          'x3-1 sq1 sq1-se3 x xi xi-cw3')},
        {...s({yaw: +45,  x: 0,                 z: sl(6) + sl(3)  },            'x4-1 sq1 sq1-nw1 x xo xo-cw4')},
        {...s({yaw: +45,  x: sl(.75),           z: sl(6) + sl(3) - sl(.75)  },  'x4-1 sq1 sq1-nw2 x xi xi-cw4')},
        {...s({yaw: -135, x: sl(3),             z: sl(6)  },                    'x2-1 sq1 sq1-nw4 x xo xo-cw2')},
        {...s({yaw: -135, x: sl(3) - sl(.75),   z: sl(6) + sl(.75)  },          'x2-1 sq1 sq1-nw3 x xi xi-cw2')},
        {...s({yaw: +135, x: sl(3),             z: sl(6) + sl(3)  },            'x1-1 sq1 sq1-se1 x xo xo-cw1')},
        {...s({yaw: +135, x: sl(3) - sl(.75),   z: sl(6) + sl(3) - sl(.75)  },  'x1-1 sq1 sq1-se2 x xi xi-cw1')},
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