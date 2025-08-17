// Dramatic Swell Pattern - Synchronized across devices
// This pattern swells up with intense brightness, flares, then dies down
// Designed for synchronized playback across multiple PixelBlaze devices

export var trigger = 1  // Start the animation
export var duration = 5  // Total duration in seconds
export var hue = 0.5  // Color hue (0-1)

var startTime = 0
var t1 = 0
var brightness = 0
var saturation = 1
var finalBrightness = 0

export function beforeRender(delta) {
  // Initialize start time on first run
  if (trigger && startTime == 0) {
    startTime = time(0.001)  // Get current time in seconds
  }
  
  // Calculate progress (0 to 1)
  t1 = (time(0.001) - startTime) / duration
  
  if (t1 > 1) {
    t1 = 1
    trigger = 0  // Animation complete
  }
  
  // Create swell curve with flare
  // 0-0.7: slow build up
  // 0.7-0.8: intense flare
  // 0.8-1.0: fade out
  
  if (t1 < 0.7) {
    // Slow exponential build
    progress = (t1 / 0.7)
    brightness = pow(progress, 2)
    saturation = 0.8 + (0.2 * progress)
  } else if (t1 < 0.8) {
    // Intense flare with slight pulsing
    flareProgress = (t1 - 0.7) / 0.1
    pulse = sin(flareProgress * PI * 4)  // Quick pulses
    brightness = 0.9 + (0.1 * pulse)
    saturation = 0.6 - (0.2 * flareProgress)  // Desaturate during flare
  } else {
    // Fade to black
    fadeProgress = (t1 - 0.8) / 0.2
    brightness = (1 - fadeProgress) * 0.8
    saturation = 0.8
  }
  
  // Add subtle wave motion
  wave = sin(t1 * PI * 2) * 0.1
  finalBrightness = brightness + wave
  
  // Clamp brightness
  if (finalBrightness > 1) finalBrightness = 1
  if (finalBrightness < 0) finalBrightness = 0
}

export function render(index) {
  // Slight variation across pixels for texture
  pixelVariation = sin(index * 0.3 + t1 * PI * 2) * 0.05
  
  hsv(hue, saturation, finalBrightness + pixelVariation)
}