import RangeTouch from '/rangetouch/dist/rangetouch.mjs'
import '/osc-js/lib/osc.min.js'

const ranges = RangeTouch.setup('input[type="range"]:not([data-raw])', { })
const osc = new OSC({plugin: new OSC.WebsocketClientPlugin({ port: 8080, host: '192.168.1.249' }) })
osc.on('open', () => console.log('OSC Connected'))
osc.on('*', msg => receiveOsc(msg))
const send = (path, ...args) => osc.send(new OSC.Message(path, ...args))
const pathToElement = {}, selectPaths = {}

// Main OSC dispatch receiver, update values and highlights of DOM elements
function receiveOsc(msg) {
    const el = pathToElement[msg.address]
    if (el) el.value = msg.args[0]
    const selections = selectPaths[msg.address]
    if (selections) {
        selections.forEach(el => el.classList.remove('selected'))
        selections.filter(el => el.arg == msg.args[0])
            .forEach(el => el.classList.add('selected'))
    }
}

// Leverage HTML / DOM tree structure for hierarchical paths and other values
function attr(el, name) {
    const abs = el.getAttribute(`data-abs-${name}`)
    if (abs) return abs
    let attr = ''
    while (el.parentNode) {
        attr = (el.getAttribute(`data-${name}`) || '') + attr
        el = el.parentNode
    }
    return attr || undefined
}

// Preprocess for speed, gather all OSC related elements
const oscElements = Array.from(document.querySelectorAll(
    '[data-path], [data-abs-path], [data-select], [data-abs-select], [data-arg]'))
'path arg select'.split(' ').forEach(prop => oscElements.forEach(el => el[prop] = attr(el, prop)))
oscElements.filter(el => el.path).forEach(el => pathToElement[el.path] = el)
const selects = oscElements.filter(el => el.select)
selects.forEach(el => selectPaths[el.select] = [])
selects.forEach(el => selectPaths[el.select].push(el))
console.log(oscElements.filter(el => el.arg).map(el => el.path + ' ' + el.arg))
const all = selector => oscElements.filter(el => el.matches(selector))

// Handle sliders movement
all('[type="range"]').forEach(
    el => el.addEventListener('input', _ => send(el.path, parseFloat(el.value))))

// Handle text / type box inputs
all('[type="text"]').forEach(
    el => el.addEventListener('change', _ => send(el.path, parseFloat(el.value))))

// Handle button presses, desktop and mobile (touch), support momentary
all('.button').forEach(el => {
    let on = attr(el, 'on'), off = attr(el, 'off')
    if (on !== undefined && off !== undefined) {
        on = parseFloat(on)
        off = parseFloat(off)
        console.log('Mapping momentary button', el.path, on, off)
        el.addEventListener('mousedown', e => send(el.path, on))
        el.addEventListener('mouseup', e => send(el.path, off))
        el.addEventListener('touchstart', e => send(el.path, on) || e.preventDefault())
        el.addEventListener('touchend', e => send(el.path, off) || e.preventDefault())
    } else {
        const arg = parseFloat(el.arg || 1)
        console.log('Mapping button', el.path, el.arg)
        el.addEventListener('click', e => send(el.path, arg))
        el.addEventListener('touchstart', e => send(el.path, arg) || e.preventDefault())
    }
})

// Grab the inital state that's been listening server side, and open OSC port
async function run() {
    const initialStateRes = await fetch('/state')
    const initialState = await initialStateRes.json()
    Object.values(initialState).forEach(msg => receiveOsc(msg))
    osc.open({ host: location.hostname, port: 8080 })
}
run()