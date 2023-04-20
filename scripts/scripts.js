let json
const read = () => json = JSON.parse(require('fs').readFileSync('/dev/stdin').toString())

const locStandard = p => ({ y: p.x, x: p.y, x: p.z }) // y x p
const locGrid     = p => ({ z: p.x, x: p.y, y: p.z }) // z x y
const locPositive = p => ({ x: p.x, y: p.y, z: -p.z }) // x y z
const locSame = p => ({ x: p.x, y: p.y, z: p.z }) // x y z



const o1 = p => ({ roll: p.yaw, yaw: p.roll, pitch: p.pitch }) // r y p
const o2 = p => ({ roll: p.yaw, pitch: p.roll, yaw: p.pitch }) // r p y
const o3 = p => ({ pitch: p.yaw, roll: p.roll, yaw: p.pitch }) // p r y
const o4 = p => ({ pitch: p.yaw, yaw: p.roll, roll: p.pitch }) // p y r
const o5 = p => ({ yaw: p.yaw, pitch: p.roll, roll: p.pitch }) // y p r
const oSame = p => ({ yaw: p.yaw, roll: p.roll, pitch: p.pitch }) // y r p

const l1 = p => ({ x: p.x, y: p.y, z: p.z }) // x y z
const lSame = p => ({ x: p.x, y: p.y, z: p.z }) // x y z

const lp1 = p => ({ x: p.x, y: p.y, z: -p.z })
const lp2 = p => ({ x: p.x, y: -p.y, z: p.z })
const lp3 = p => ({ x: -p.x, y: p.y, z: p.z })

const op1 = p => ({ yaw: p.yaw, roll: p.roll, pitch: -p.pitch }) // y r p
const op2 = p => ({ yaw: p.yaw, roll: -p.roll, pitch: p.pitch }) // y r p
const op3 = p => ({ yaw: -p.yaw, roll: p.roll, pitch: p.pitch }) // y r p

const plus90 = p => ({ yaw: p.yaw + 90 })

const xformProject = (xform) => json.model.fixtures.forEach(f => Object.assign(f.parameters, xform(f.parameters)))

const dir1 = p => ({ roll: p.pitch, pitch: p.roll })
const dir2 = p => ({ roll: p.yaw, yaw: p.roll })
const dir3 = p => ({ yaw: p.pitch, pitch: p.yaw })
const dir4 = p => ({ yaw: p.roll, roll: p.yaw })
const dir5 = p => ({ pitch: p.roll, roll: p.pitch })
const dir6 = p => ({ pitch: p.yaw, yaw: p.pitch })


const locSwitchXY = p => ({ y: p.x, x: p.y })
function xform() { xformProject(locSwitchXY) ; xformProject(oSame) }

// based on shown axis in LXS, it is a LEFT HANDED COORDINATE SYSTEM (positive z *LEFT* thumb, positive y curled fingers, positive x hand)
// probably common in game / graphics libraries
// https://learn.microsoft.com/en-us/previous-versions/windows/desktop/bb324490(v=vs.85)
// probs wrong / illogical: negating one of xyz, and another of yaw pitch roll, these: z => pitch, y => roll, x => yaw

read()
json.model.fixtures = json.model.fixtures.filter(f => f.parameters.x == 0 && f.parameters.y == 0 && f.parameters.z == 0)
xform()

console.log(JSON.stringify(json, null, 2))
