/* 
Fiery Eye of Sauron (as seen in The Lord of the Rings Movies).

2022 Ben Hencke (wizard)
*/

var rgbGradient = [
  0,    0, 0, 0,
  0.2,  1, 0, 0,
  0.8,  1, 1, 0,
  1,    1, 1, 1
]
setPalette(rgbGradient)
export var aDensity = 7, rDensity = 1, dilation = 1.1, slitness = 4

export function sliderAngularDensity(v) {
  aDensity = 2 + round(v * 16)
}

export function sliderRadialDensity(v) {
  rDensity = .1 + (v * 2)
}

export function sliderDialation(v) {
  dilation = 0.7 + v 
}

export function sliderSlitness(v) {
  slitness = 1 + v*4
}

export function beforeRender(delta) {
  //perlin wraps smoothly every 256, so 0.0 and 256 are the same
  //animate the perlin noise by moving z across time from 0-256
  //this also means increasing the interval we use with time()
  //and happens to give us over 7.6 minutes of unique noise
  morphTime = time(7) * 256
  rTime = time(3) * 256

  resetTransform()
  s = 3
  translate(-.5, -.5)
  scale(s,s * 1.4)
  setPerlinWrap(aDensity, 0, 0)
}
export function render2D(index, x, y) {
  //calc radial coordinates
  r = hypot(x, y)
  a = (atan2(y, x) + PI) / PI2
  
  //use ridge noise for wispy fire tendrils. animate outward, with a slow morph
  v = perlinRidge(a * aDensity,r * rDensity - rTime , morphTime, 2, .5, 1.1, 3)
  
  //fade out in an oval shape, more sharply towards the edge
  r2 = clamp((s-1)-r, 0, 1)
  r2 = 2-r2*r2
  v = v*min((2-r2), 1)
  
  //darken the middle for an evil slit pupil
  v = v - max(0,dilation - hypot(x*slitness, y))
  
  v = min(v,1) //keep palette from wrapping
  paint(v, v)
}