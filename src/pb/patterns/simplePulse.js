// Simple red pulse - fade up, hold at full red, fade down

export function beforeRender(delta) {
  t1 = time(0.05)
  // Plateau at full brightness: fade up, hold at 1, fade down
  if (t1 < 0.3) {
    brightness = t1 / 0.3  // Fade up for first 30%
  } else if (t1 < 0.7) {
    brightness = 1  // Stay at full red for middle 40%
  } else {
    brightness = (1 - t1) / 0.3  // Fade down for last 30%
  }
}

export function render(index) {
  hsv(0, 1, brightness)  // Hue 0 = red, full saturation, variable brightness
}