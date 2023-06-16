/*
Attempt adding some missing Pixelblaze pattern functions
*/

function mod(x, y) {
    var modulo = x % y;
    return Math.sign(y) == Math.sign(modulo) ? modulo : y + modulo;
}

// auto generated delegators:
function setPalette(a,b,c,d,e,f,g) { return __pattern.setPalette(a,b,c,d,e,f,g); }
function resetTransform(a,b,c,d,e,f,g) { return __pattern.resetTransform(a,b,c,d,e,f,g); }
function setPerlinWrap(a,b,c,d,e,f,g) { return __pattern.setPerlinWrap(a,b,c,d,e,f,g); }
function perlinRidge(a,b,c,d,e,f,g) { return __pattern.perlinRidge(a,b,c,d,e,f,g); }
function scale(a,b,c,d,e,f,g) { return __pattern.scale(a,b,c,d,e,f,g); }
function translate(a,b,c,d,e,f,g) { return __pattern.translate(a,b,c,d,e,f,g); }
// no args
function clockYear() { return __pattern.clockYear(); }
function clockMonth() { return __pattern.clockMonth(); }
function clockDay() { return __pattern.clockDay(); }
function clockHour() { return __pattern.clockHour(); }
function clockMinute() { return __pattern.clockMinute(); }
function clockSecond() { return __pattern.clockSecond(); }
function clockWeekday() { return __pattern.clockWeekday(); }

function setPalette(array) {
    return __pattern.setPalette(array);
}

function paint(value, brightness = 1) {
  return (__color = __pattern.paint(value, brightness));
}

function setPerlinWrap(x, y, z) {
    return __pattern.setPerlinWrap(x, y, z);
}

function perlinRidge(x, y, z, lacunarity, gain, offset, octaves) {
    return __pattern.perlinRidge(x, y, z, lacunarity, gain, offset, octaves);
}

function resetTransform() {
    return __pattern.resetTransform();
}

function scale(x, y, z) {
    return __pattern.scale(x, y, z);
}

function translate(x, y, z) {
    return __pattern.translate(x, y, z);
}
