/*
Attempt adding some missing Pixelblaze pattern functions
*/

// auto generated delegators (see notes.md and PixelblazeHelper.java):
function resetTransform() { __pattern.resetTransform() ; }
function scale(x,y,z) { __pattern.scale(x,y,z) ; }
function translate(x,y,z) { __pattern.translate(x,y,z) ; }
function rotate(v) { __pattern.rotate(v); }
function perlinRidge(x,y,z,lacunarity,gain,offset,octaves) { __pattern.perlinRidge(x,y,z,lacunarity,gain,offset,octaves) ; }
function perlinTurbulence(x,y,z,lacunarity,gain,octaves) { __pattern.perlinTurbulence(x,y,z,lacunarity,gain,octaves) ; }
function perlinFbm(x,y,z,lacunarity,gain,octaves) { __pattern.perlinFbm(x,y,z,lacunarity,gain,octaves) ; }
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
function infoLog(msg) { __pattern.log(msg) ; }


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

function log2(y) {
    return Math.log(y) / Math.log(2);
}

function trunc(v) {
    return v - v % 1;
}
function frac(v) {
    return v - trunc(v);
}

function mix(low, high, weight) {
    return low + (high - low) * weight;
}

// fake io
var INPUT = 0, INPUT_PULLUP = 1, INPUT_PULLDOWN = 2, OUTPUT = 3, OUTPUT_OPEN_DRAIN = 4, ANALOG = 5, HIGH = 6;
var pinMode = INPUT;

// what could go wrong?
Array.prototype.sum = function() { return this.reduce((partialSum, v) => partialSum + v, 0); }
function arraySum(arr) { return arr.sum(); };

Array.prototype.mutate = function(fn) {
    for (var index = 0; index < this.length; index++) {
        this[index] = fn(this[index], index, this);
    }
}
function arrayMutate(arr, fn) { arr.mutate(fn); }

Array.prototype.mapTo = function(dest, fn) {
    for (var index = 0; index < this.length; index++) {
        var val = fn(this[index], index, this);
        if (dest.length > index) {
            dest[index] = val;
        }
    }
}
function arrayMapTo(arr, dest, fn) { arr.mapTo(dest, fn); }

function arraySortBy(arr, fn) { return arr.sort(fn); }


Math.sign = function(v) { return v > 0.0 ? 1.0 : v < 0.0 ? -1.0 : 0.0 ; }
//function array(len) { return new Array(len) ; }