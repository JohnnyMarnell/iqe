const fs = require('fs')

// yaw, pitch, roll, (0,0,0) => along x axis, (0,90,0) => no visual change (so x axis?),
//      (0,0,90) vertical up (y+) (so z axis?)
let id = 100
const numLedsPerStrip = 140
const ledSpacing = 5
const stripLen = numLedsPerStrip * ledSpacing // 700 == 5 spacing * 140 LED pixels / "numPoints"
const numRafters = 72
const numPillars = 0
// const controllerIP = "192.168.0.10"
// const controllerIP = "169.254.250.112"
const controllerIP = "127.0.0.1"

// const mapStripToArtnetPair = index => index * 3
const mapStripToArtnetPair = index => (index + 1) * 3

const s = defaultNagBugglerSaberOfLight
const sl = stripLenMultiplier => stripLenMultiplier * stripLen

/** Notes on fArtNet. The Advatek PixLite E16-s mk3 has 32 outputs, for which we configure start + ends for 
 * universe and channel. A channel represents one of 3 color components (RGB) of an actual LED pixel, thus
 * for 140 LEDs, we need 3 * 140 == 420 (blaze that shit, brah) channels. At each output, the channel start
 * and end is 1 to 510, thus the pixel channels need to be striped, since 510 is a limit of the controller
 * in "expanded/non-expanded modes". Because of this striping, fArtNet start and end universes will look like
 * 1-3, 4-6, 7-9 etc, and the start and end channel will always be full 1-510. So each actual NagBuggler LED
 * Saber of Light Strip Fixture in LX must be mapped to the correct channel position in the
 * current output stripe (which should repeat as 0, 420, 330, 0 ...), and universes follow pattern
 *  (N, N, N + 1,   N + 3, N + 3, N + 4,   ), or (repeat last, up by 1, up by 2)
 */
const universeHyperspaceWarp = [2, 0, 1], channelingus = [0, 420, 330]
let universe = -1
const fArtNetPairs = []
for (let i = 0; i < 1024; i++) {
    universe += universeHyperspaceWarp[i % 3]
    fArtNetPairs.push( [universe, channelingus[i % 3] ] )
}

function buildNagBugglerSaberOfLightFixtures() {
    const vSpace = .15, hSpace = .1
    return [
        {...s({yaw: -90, x: sl(24 * vSpace), y: sl(1), z: 0}, 'r-v2-24 sq2 col1')},
        {...s({yaw: -90, x: sl(23 * vSpace), y: sl(1), z: 0}, 'r-v2-23 sq2 col1')},
        {...s({yaw: -90, x: sl(22 * vSpace), y: sl(1), z: 0}, 'r-v2-22 sq2 col1')},
        {...s({yaw: -90, x: sl(21 * vSpace), y: sl(1), z: 0}, 'r-v2-21 sq2 col1')},
        {...s({yaw: -90, x: sl(20 * vSpace), y: sl(1), z: 0}, 'r-v2-20 sq2 col1')},
        {...s({yaw: -90, x: sl(19 * vSpace), y: sl(1), z: 0}, 'r-v2-19 sq2 col1')},
        {...s({yaw: -90, x: sl(18 * vSpace), y: sl(1), z: 0}, 'r-v2-18 sq2 col1')},
        {...s({yaw: -90, x: sl(17 * vSpace), y: sl(1), z: 0}, 'r-v2-17 sq2 col1')},
        {...s({yaw: -90, x: sl(16 * vSpace), y: sl(1), z: 0}, 'r-v2-16 sq2 col1')},
        {...s({yaw: -90, x: sl(15 * vSpace), y: sl(1), z: 0}, 'r-v2-15 sq2 col1')},
        {...s({yaw: -90, x: sl(14 * vSpace), y: sl(1), z: 0}, 'r-v2-14 sq2 col1')},
        {...s({yaw: -90, x: sl(13 * vSpace), y: sl(1), z: 0}, 'r-v2-13 sq2 col1')},
        {...s({yaw: -90, x: sl(12 * vSpace), y: sl(1), z: 0}, 'r-v2-12 sq2 col1')},
        {...s({yaw: -90, x: sl(11 * vSpace), y: sl(1), z: 0}, 'r-v2-11 sq2 col1')},
        {...s({yaw: -90, x: sl(10 * vSpace), y: sl(1), z: 0}, 'r-v2-10 sq2 col1')},
        {...s({yaw: -90, x: sl(9  * vSpace), y: sl(1), z: 0}, 'r-v2-9  sq2 col1')},
        {...s({yaw: -90, x: sl(8  * vSpace), y: sl(1), z: 0}, 'r-v2-8  sq2 col1')},
        {...s({yaw: -90, x: sl(7  * vSpace), y: sl(1), z: 0}, 'r-v2-7  sq2 col1')},
        {...s({yaw: -90, x: sl(6  * vSpace), y: sl(1), z: 0}, 'r-v2-6  sq2 col1')},
        {...s({yaw: -90, x: sl(5  * vSpace), y: sl(1), z: 0}, 'r-v2-5  sq2 col1')},
        {...s({yaw: -90, x: sl(4  * vSpace), y: sl(1), z: 0}, 'r-v2-4  sq2 col1')},
        {...s({yaw: -90, x: sl(3  * vSpace), y: sl(1), z: 0}, 'r-v2-3  sq2 col1')},
        {...s({yaw: -90, x: sl(2  * vSpace), y: sl(1), z: 0}, 'r-v2-2  sq2 col1')},
        {...s({yaw: -90, x: sl(1  * vSpace), y: sl(1), z: 0}, 'r-v2-1  sq2 col1')},

        {...s({yaw: -90, x: sl(24 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-24 sq2 col2')},
        {...s({yaw: -90, x: sl(23 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-23 sq2 col2')},
        {...s({yaw: -90, x: sl(22 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-22 sq2 col2')},
        {...s({yaw: -90, x: sl(21 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-21 sq2 col2')},
        {...s({yaw: -90, x: sl(20 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-20 sq2 col2')},
        {...s({yaw: -90, x: sl(19 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-19 sq2 col2')},
        {...s({yaw: -90, x: sl(18 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-18 sq2 col2')},
        {...s({yaw: -90, x: sl(17 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-17 sq2 col2')},
        {...s({yaw: -90, x: sl(16 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-16 sq2 col2')},
        {...s({yaw: -90, x: sl(15 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-15 sq2 col2')},
        {...s({yaw: -90, x: sl(14 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-14 sq2 col2')},
        {...s({yaw: -90, x: sl(13 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-13 sq2 col2')},
        {...s({yaw: -90, x: sl(12 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-12 sq2 col2')},
        {...s({yaw: -90, x: sl(11 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-11 sq2 col2')},
        {...s({yaw: -90, x: sl(10 * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-10 sq2 col2')},
        {...s({yaw: -90, x: sl(9  * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-9  sq2 col2')},
        {...s({yaw: -90, x: sl(8  * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-8  sq2 col2')},
        {...s({yaw: -90, x: sl(7  * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-7  sq2 col2')},
        {...s({yaw: -90, x: sl(6  * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-6  sq2 col2')},
        {...s({yaw: -90, x: sl(5  * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-5  sq2 col2')},
        {...s({yaw: -90, x: sl(4  * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-4  sq2 col2')},
        {...s({yaw: -90, x: sl(3  * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-3  sq2 col2')},
        {...s({yaw: -90, x: sl(2  * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-2  sq2 col2')},
        {...s({yaw: -90, x: sl(1  * vSpace), y: sl(1), z: sl(1 + 1 * hSpace)}, 'r-v2-1  sq2 col2')},

        {...s({yaw: -90, x: sl(24 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-24 sq2 col3')},
        {...s({yaw: -90, x: sl(23 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-23 sq2 col3')},
        {...s({yaw: -90, x: sl(22 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-22 sq2 col3')},
        {...s({yaw: -90, x: sl(21 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-21 sq2 col3')},
        {...s({yaw: -90, x: sl(20 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-20 sq2 col3')},
        {...s({yaw: -90, x: sl(19 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-19 sq2 col3')},
        {...s({yaw: -90, x: sl(18 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-18 sq2 col3')},
        {...s({yaw: -90, x: sl(17 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-17 sq2 col3')},
        {...s({yaw: -90, x: sl(16 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-16 sq2 col3')},
        {...s({yaw: -90, x: sl(15 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-15 sq2 col3')},
        {...s({yaw: -90, x: sl(14 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-14 sq2 col3')},
        {...s({yaw: -90, x: sl(13 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-13 sq2 col3')},
        {...s({yaw: -90, x: sl(12 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-12 sq2 col3')},
        {...s({yaw: -90, x: sl(11 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-11 sq2 col3')},
        {...s({yaw: -90, x: sl(10 * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-10 sq2 col3')},
        {...s({yaw: -90, x: sl(9  * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-9  sq2 col3')},
        {...s({yaw: -90, x: sl(8  * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-8  sq2 col3')},
        {...s({yaw: -90, x: sl(7  * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-7  sq2 col3')},
        {...s({yaw: -90, x: sl(6  * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-6  sq2 col3')},
        {...s({yaw: -90, x: sl(5  * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-5  sq2 col3')},
        {...s({yaw: -90, x: sl(4  * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-4  sq2 col3')},
        {...s({yaw: -90, x: sl(3  * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-3  sq2 col3')},
        {...s({yaw: -90, x: sl(2  * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-2  sq2 col3')},
        {...s({yaw: -90, x: sl(1  * vSpace), y: sl(1), z: sl(2 + 2 * hSpace)}, 'r-v2-1  sq2 col3')},

        // {...s({yaw: -90, x: sl(0  * vSpace), y: sl(1), z: sl(-(1 + hSpace))}, 'r-v2-t1 sq1')},
        // {...s({yaw: -90, x: sl(0  * vSpace), y: sl(1), z: sl(0)},             'r-v2-t2 sq2')},
        // {...s({yaw: -90, x: sl(0  * vSpace), y: sl(1), z: sl(+(1 + hSpace))}, 'r-v2-t3 sq3')},
    ]
}

function buildNagBugglerSaberOfLightFixtures_v1() {
    return [
        /* 
            Tags for membership (shapes/outlines/sets), and directional order progression therein
                (e.g. clockwise [first, 1, starts upper left / northwest corner], east, south,
                 diagonals moving southeast and northwest, etc)
            pc, po, pi, ps, pn, pm: pillar columns (running N to S), outer, inner, rows (W to E) south, north, middle
            e.g. pc4-s2 means the second pillar progressing southward through 4th pillar column
            Per the data/power diagrams, West to East progression in general increases numerically (e.g. squares 1 - 3)

            PILLARS #0 - #20:
            Going east to west, 7 pillar columns of 3 south to north (x+)
            temp: 4, 3, 2, 1 becomes 7, 5, 3, 1
        */
        {...s({roll: -90, x: sl(0  ), z: sl(0 * 1.5)}, 'pc7 pc7-s3 ps ps-e7 po po-cw9 sq3 sq3-cw5')},
        {...s({roll: -90, x: sl(1.5), z: sl(0 * 1.5)}, 'pc7 pc7-s2 pm pm-e7 po po-cw8 sq3 sq3-cw4')},
        {...s({roll: -90, x: sl(3  ), z: sl(0 * 1.5)}, 'pc7 pc7-s1 pn pn-e7 po po-cw7 sq3 sq3-cw3')},

        {...s({roll: -90, x: sl(0  ), z: sl(1 * 1.5)}, 'pc6 pc6-s3 ps ps-e6 po po-cw10 sq3 sq3-cw6')},
        {...s({roll: -90, x: sl(1.5), z: sl(1 * 1.5)}, 'pc6 pc6-s2 pm pm-e6 pi pi-e5   sq3        ')},
        {...s({roll: -90, x: sl(3  ), z: sl(1 * 1.5)}, 'pc6 pc6-s1 pn pn-e6 po po-cw6  sq3 sq3-cw2')},

        {...s({roll: -90, x: sl(0  ), z: sl(2 * 1.5)}, 'pc5 pc5-s3 ps ps-e5 po po-cw11 sq3 sq3-cw7 sq2 sq2-cw5')},
        {...s({roll: -90, x: sl(1.5), z: sl(2 * 1.5)}, 'pc5 pc5-s2 pm pm-e5 pi pi-e4   sq3 sq3-cw8 sq2 sq2-cw4')},
        {...s({roll: -90, x: sl(3  ), z: sl(2 * 1.5)}, 'pc5 pc5-s1 pn pn-e5 po po-cw5  sq3 sq3-cw1 sq2 sq2-cw3')},

        {...s({roll: -90, x: sl(0  ), z: sl(3 * 1.5)}, 'pc4 pc4-s3 ps ps-e4 po po-cw12 sq2 sq2-cw6')},
        {...s({roll: -90, x: sl(1.5), z: sl(3 * 1.5)}, 'pc4 pc4-s2 pm pm-e4 pi pi-e3   sq2        ')},
        {...s({roll: -90, x: sl(3  ), z: sl(3 * 1.5)}, 'pc4 pc4-s1 pn pn-e4 po po-cw4  sq2 sq2-cw2')},

        {...s({roll: -90, x: sl(0  ), z: sl(4 * 1.5)}, 'pc3 pc3-s3 ps ps-e3 po po-cw13 sq2 sq2-cw7 sq1 sq1-cw5')},
        {...s({roll: -90, x: sl(1.5), z: sl(4 * 1.5)}, 'pc3 pc3-s2 pm pm-e3 pi pi-e2   sq2 sq2-cw8 sq1 sq1-cw4')},
        {...s({roll: -90, x: sl(3  ), z: sl(4 * 1.5)}, 'pc3 pc3-s1 pn pn-e3 po po-cw3  sq2 sq2-cw1 sq1 sq1-cw3')},

        {...s({roll: -90, x: sl(0  ), z: sl(5 * 1.5)}, 'pc2 pc2-s3 ps ps-e2 po po-cw12 sq1 sq1-cw6')},
        {...s({roll: -90, x: sl(1.5), z: sl(5 * 1.5)}, 'pc2 pc2-s2 pm pm-e2 pi pi-e1   sq1        ')},
        {...s({roll: -90, x: sl(3  ), z: sl(5 * 1.5)}, 'pc2 pc2-s1 pn pn-e2 po po-cw4  sq1 sq1-cw2')},

        {...s({roll: -90, x: sl(0  ), z: sl(6 * 1.5)}, 'pc1 pc1-s3 ps ps-e1 po po-cw15 sq1 sq1-cw7')},
        {...s({roll: -90, x: sl(1.5), z: sl(6 * 1.5)}, 'pc1 pc1-s2 pm pm-e1 po po-cw16 sq1 sq1-cw8')},
        {...s({roll: -90, x: sl(3  ), z: sl(6 * 1.5)}, 'pc1 pc1-s1 pn pn-e1 po po-cw1  sq1 sq1-cw1')},

    
        // CEILING RAFTERS, #21 - #29:
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

        // #30 - #38
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
        // #39 - #41
        {...s({yaw: 180, x: sl(1), z: sl(0 * 3)}, 'rc4 rc4-s3 sq3 sq3-cw6')},
        {...s({yaw: 180, x: sl(2), z: sl(0 * 3)}, 'rc4 rc4-s2 sq3 sq3-cw5')},
        {...s({yaw: 180, x: sl(3), z: sl(0 * 3)}, 'rc4 rc4-s1 sq3 sq3-cw4')},
        // #42 - #44
        {...s({yaw: 180, x: sl(1), z: sl(1 * 3)}, 'rc3 rc1-s3 sq2 sq2-cw6 sq3 sq3-cw10')},
        {...s({yaw: 180, x: sl(2), z: sl(1 * 3)}, 'rc3 rc1-s2 sq2 sq2-cw5 sq3 sq3-cw11')},
        {...s({yaw: 180, x: sl(3), z: sl(1 * 3)}, 'rc3 rc1-s1 sq2 sq2-cw4 sq3 sq3-cw12')},
        // #45 - #47
        {...s({yaw: 180, x: sl(1), z: sl(2 * 3)}, 'rc2 rc1-s3 sq1 sq1-cw6 sq2 sq2-cw10')},
        {...s({yaw: 180, x: sl(2), z: sl(2 * 3)}, 'rc2 rc1-s2 sq1 sq1-cw5 sq2 sq2-cw11')},
        {...s({yaw: 180, x: sl(3), z: sl(2 * 3)}, 'rc2 rc1-s1 sq1 sq1-cw4 sq2 sq2-cw12')},
        // #48 - #50
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
        // #51 - #58
        {...s({yaw: -45,  x: 0,                 z: 0  },                        'x3-3 sq3 sq3-se4 x xo xo-cw3')},
        {...s({yaw: -45,  x: sl(.75),           z: sl(.75)  },                  'x3-3 sq3 sq3-se3 x xi xi-cw3')},
        {...s({yaw: +45,  x: 0,                 z: sl(3)  },                    'x4-3 sq3 sq3-nw1 x xo xo-cw4')},
        {...s({yaw: +45,  x: sl(.75),           z: sl(3) - sl(.75)  },          'x4-3 sq3 sq3-nw2 x xi xi-cw4')},
        {...s({yaw: -135, x: sl(3),             z: 0  },                        'x2-3 sq3 sq3-nw4 x xo xo-cw2')},
        {...s({yaw: -135, x: sl(3) - sl(.75),   z: sl(.75)  },                  'x2-3 sq3 sq3-nw3 x xi xi-cw2')},
        {...s({yaw: +135, x: sl(3),             z: sl(3)  },                    'x1-3 sq3 sq3-se1 x xo xo-cw1')},
        {...s({yaw: +135, x: sl(3) - sl(.75),   z: sl(3) - sl(.75)  },          'x1-3 sq3 sq3-se2 x xi xi-cw1')},

        // #59 - #60
        {...s({yaw: -45,  x: 0,                 z: sl(3)  },                    'x3-2 sq2 sq2-se4 x xo xo-cw3')},
        {...s({yaw: -45,  x: sl(.75),           z: sl(3) + sl(.75)  },          'x3-2 sq2 sq2-se3 x xi xi-cw3')},
        {...s({yaw: +45,  x: 0,                 z: sl(3) + sl(3)  },            'x4-2 sq2 sq2-nw1 x xo xo-cw4')},
        {...s({yaw: +45,  x: sl(.75),           z: sl(3) + sl(3) - sl(.75)  },  'x4-2 sq2 sq2-nw2 x xi xi-cw4')},
        {...s({yaw: -135, x: sl(3),             z: sl(3)  },                    'x2-2 sq2 sq2-nw4 x xo xo-cw2')},
        {...s({yaw: -135, x: sl(3) - sl(.75),   z: sl(3) + sl(.75)  },          'x2-2 sq2 sq2-nw3 x xi xi-cw2')},
        {...s({yaw: +135, x: sl(3),             z: sl(3) + sl(3)  },            'x1-2 sq2 sq2-se1 x xo xo-cw1')},
        {...s({yaw: +135, x: sl(3) - sl(.75),   z: sl(3) + sl(3) - sl(.75)  },  'x1-2 sq2 sq2-se2 x xi xi-cw1')},

        // #67 - #74
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
const path = `${__dirname}/../../iqe.lxp`
const project = JSON.parse(fs.readFileSync(path))
project.model.fixtures = buildNagBugglerSaberOfLightFixtures()
console.log(JSON.stringify(project, null, 2))
console.error(`Regenerated ${project.model.fixtures.length} fixtures`)
fs.writeFileSync(path, JSON.stringify(project, null, 2))

function defaultNagBugglerSaberOfLight(params, tags) {
    id++
    const i = id - 101
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
            label: (id - 100 <= numPillars ? `Pillar ${id - 100}` : `Rafter ${id - 100 - numPillars}`) + '; #' + i,
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
            host: controllerIP,
            port: 7890,
            artNetUniverse: fArtNetPairs[mapStripToArtnetPair(i)][0],
            dmxChannel: fArtNetPairs[mapStripToArtnetPair(i)][1],
            artNetSequenceEnabled: false,
            opcChannel: 0,
            opcOffset: 0,
            ddpDataOffset: 0,
            kinetPort: 1,
            numPoints: numLedsPerStrip,
            spacing: ledSpacing,
            
            // overlay any overriding params from above!
            ...params
        },
        children: {}
    }
}