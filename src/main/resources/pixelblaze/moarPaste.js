/*
Attempt adding some missing Pixelblaze pattern functions
*/

// auto generated delegators (see notes.md and PixelblazeHelper.java):
function resetTransform() { __pattern.resetTransform() ; }
function scale(x,y,z) { __pattern.scale(x,y,z) ; }
function translate(x,y,z) { __pattern.translate(x,y,z) ; }
function perlinRidge(x,y,z,lacunarity,gain,offset,octaves) { __pattern.perlinRidge(x,y,z,lacunarity,gain,offset,octaves) ; }
function perlinTurbulence(x,y,z,lacunarity,gain,octaves) { __pattern.perlinTurbulence(x,y,z,lacunarity,gain,octaves) ; }
function setPerlinWrap(x,y,z) { __pattern.setPerlinWrap(x,y,z) ; }
function smoothstep(min,max,val) { __pattern.smoothstep(min,max,val) ; }
function setPalette(array) { __pattern.setPalette(array) ; }
function getGradientColor(lerp) { __pattern.getGradientColor(lerp) ; }
function paint(lerp,brightness) { __pattern.paint(lerp,brightness) ; }
function clockYear() { __pattern.clockYear() ; }
function clockMonth() { __pattern.clockMonth() ; }
function clockDay() { __pattern.clockDay() ; }
function clockWeekday() { __pattern.clockWeekday() ; }
function clockHour() { __pattern.clockHour() ; }
function clockMinute() { __pattern.clockMinute() ; }
function clockSecond() { __pattern.clockSecond() ; }
function log(msg) { __pattern.log(msg) ; }


function paint(value, brightness = 1) {
  return (__color = __pattern.paint(value, brightness));
}

function mod(x, y) {
    var modulo = x % y;
    return Math.sign(y) == Math.sign(modulo) ? modulo : y + modulo;
}

function square(v) {
  v = v % 1;
  return v < 0.5 ? 1 : 0;
}

// fake io
var INPUT = 0, INPUT_PULLUP = 1, INPUT_PULLDOWN = 2, OUTPUT = 3, OUTPUT_OPEN_DRAIN = 4, ANALOG = 5;

// what could go wrong?
Array.prototype.sum = function() { return this.reduce((partialSum, v) => partialSum + v, 0); }
Math.sign = function(v) { return v > 0.0 ? 1.0 : v < 0.0 ? -1.0 : 0.0 ; }