#!/usr/bin/env python3
"""
PixelBlaze Pattern Library
Collection of patterns for synchronized effects
"""

# Synchronized Pulse Pattern
# This pattern creates a smooth breathing effect with configurable color
SYNC_PULSE_PATTERN = """
// IQE Synchronized Pulse Pattern
// Creates a smooth breathing glow effect
// All devices will pulse in sync when triggered together

// Export these so they can be set via API
export var hue = 0.5  // Color hue (0-1)
export var pulseSpeed = 2  // Pulses per second
export var minBrightness = 0.1  // Minimum brightness
export var maxBrightness = 1.0  // Maximum brightness

// Time tracking for smooth animation
var startTime = 0
var initialized = false

export function beforeRender(delta) {
  if (!initialized) {
    startTime = time(0.001)  // Get time in seconds
    initialized = true
  }
  
  // Calculate elapsed time for synchronized pulsing
  t1 = time(0.001) - startTime
  
  // Create sine wave for smooth pulsing
  // Using a sine wave ensures smooth transitions
  wave = (sin(t1 * pulseSpeed * PI2) + 1) / 2
  
  // Map wave to brightness range
  pulseBrightness = minBrightness + (maxBrightness - minBrightness) * wave
}

export function render(index) {
  // All pixels show the same color and brightness
  // This creates a unified pulse effect across the entire strip
  hsv(hue, 1, pulseBrightness)
}

// 2D version for matrix displays
export function render2D(index, x, y) {
  hsv(hue, 1, pulseBrightness)
}

// 3D version for volumetric displays
export function render3D(index, x, y, z) {
  hsv(hue, 1, pulseBrightness)
}
"""

# Flash Alert Pattern
# Quick flash to get attention
FLASH_ALERT_PATTERN = """
// IQE Flash Alert Pattern
// Creates a quick flash effect for notifications

export var hue = 0.1  // Yellow by default
export var flashDuration = 0.5  // Duration in seconds
export var flashCount = 3  // Number of flashes

var startTime = 0
var initialized = false

export function beforeRender(delta) {
  if (!initialized) {
    startTime = time(0.001)
    initialized = true
  }
  
  t1 = time(0.001) - startTime
  
  // Calculate which flash we're on
  flashNumber = floor(t1 / flashDuration)
  
  // Stop after specified number of flashes
  if (flashNumber >= flashCount * 2) {
    brightness = 0
  } else {
    // Alternate between on and off
    brightness = (flashNumber % 2) == 0 ? 1 : 0
  }
}

export function render(index) {
  hsv(hue, 1, brightness)
}

export function render2D(index, x, y) {
  hsv(hue, 1, brightness)
}

export function render3D(index, x, y, z) {
  hsv(hue, 1, brightness)
}
"""

# Rainbow Wave Pattern
# Synchronized rainbow that moves across all devices
RAINBOW_WAVE_PATTERN = """
// IQE Rainbow Wave Pattern
// Synchronized rainbow effect across devices

export var speed = 0.5  // Wave speed
export var wavelength = 1  // How many rainbows fit on the strip

var startTime = 0
var initialized = false

export function beforeRender(delta) {
  if (!initialized) {
    startTime = time(0.001)
    initialized = true
  }
  
  t1 = time(0.001) - startTime
}

export function render(index) {
  // Create rainbow based on position and time
  h = (index / pixelCount * wavelength + t1 * speed) % 1
  hsv(h, 1, 1)
}

export function render2D(index, x, y) {
  // For 2D, use distance from center
  h = (hypot(x - 0.5, y - 0.5) * wavelength + t1 * speed) % 1
  hsv(h, 1, 1)
}

export function render3D(index, x, y, z) {
  // For 3D, use distance from origin
  h = (hypot(x, y, z) * wavelength + t1 * speed) % 1
  hsv(h, 1, 1)
}
"""

# Pattern metadata
PATTERNS = {
    "sync_pulse": {
        "name": "IQE Sync Pulse",
        "code": SYNC_PULSE_PATTERN,
        "description": "Synchronized breathing pulse",
        "parameters": {
            "hue": {"min": 0, "max": 1, "default": 0.5},
            "pulseSpeed": {"min": 0.5, "max": 5, "default": 2},
            "minBrightness": {"min": 0, "max": 0.5, "default": 0.1},
            "maxBrightness": {"min": 0.5, "max": 1, "default": 1.0}
        }
    },
    "flash_alert": {
        "name": "IQE Flash Alert",
        "code": FLASH_ALERT_PATTERN,
        "description": "Quick flash for notifications",
        "parameters": {
            "hue": {"min": 0, "max": 1, "default": 0.1},
            "flashDuration": {"min": 0.1, "max": 2, "default": 0.5},
            "flashCount": {"min": 1, "max": 10, "default": 3}
        }
    },
    "rainbow_wave": {
        "name": "IQE Rainbow Wave",
        "code": RAINBOW_WAVE_PATTERN,
        "description": "Synchronized rainbow wave",
        "parameters": {
            "speed": {"min": 0.1, "max": 2, "default": 0.5},
            "wavelength": {"min": 0.5, "max": 5, "default": 1}
        }
    }
}

def get_pattern(pattern_key: str) -> dict:
    """Get a pattern by key"""
    return PATTERNS.get(pattern_key, None)

def list_patterns() -> list:
    """List all available patterns"""
    return [
        {"key": key, "name": data["name"], "description": data["description"]}
        for key, data in PATTERNS.items()
    ]