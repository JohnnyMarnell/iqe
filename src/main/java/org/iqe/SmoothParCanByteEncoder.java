package org.iqe;

import heronarts.lx.output.LXBufferOutput;
import heronarts.lx.output.LXOutput;
import heronarts.lx.color.LXColor;
import java.util.HashMap;
import java.util.Map;

/**
 * Smoothed ByteEncoder for 7-channel DMX ParCans
 * Uses HSV space smoothing with rate limiting for fluid transitions
 * Prevents jumpy/strobe-like effects on spot lights
 */
public class SmoothParCanByteEncoder implements LXBufferOutput.ByteEncoder {
    
    // Always output 7 bytes per pixel
    private static final int NUM_BYTES = 7;
    
    // Smoothing factor (0 = no smoothing, 1 = infinite smoothing)
    // Start with moderate smoothing - can be tuned
    private float smoothingFactor = 0.85f;
    
    // Store smoothed HSV values per offset (for multiple ParCans)
    // Format: [hue (0-360), saturation (0-100), value/brightness (0-100)]
    private Map<Integer, float[]> smoothedHSV = new HashMap<>();
    
    // Maximum rate of change per frame (in HSV units)
    // These prevent large jumps even when smoothing is lower
    private static final float MAX_HUE_CHANGE = 15.0f;  // degrees per frame
    private static final float MAX_SAT_CHANGE = 8.0f;   // percent per frame  
    private static final float MAX_VAL_CHANGE = 10.0f;  // percent per frame
    
    public SmoothParCanByteEncoder() {
        this(0.85f);
    }
    
    public SmoothParCanByteEncoder(float smoothingFactor) {
        this.smoothingFactor = Math.max(0.7f, Math.min(smoothingFactor, 0.99f));
    }
    
    @Override
    public int getNumBytes() {
        return NUM_BYTES;
    }
    
    @Override
    public void writeBytes(int color, LXOutput.GammaTable.Curve gamma, byte[] output, int offset) {
        // Convert target color to HSV for smoother transitions
        float targetH = LXColor.h(color);  // 0-360
        float targetS = LXColor.s(color);  // 0-100
        float targetV = LXColor.b(color);  // 0-100 (brightness/value)
        
        // Get or initialize smoothed HSV values for this offset
        float[] smoothed = smoothedHSV.computeIfAbsent(offset, k -> new float[]{targetH, targetS, targetV});
        
        // Calculate desired changes
        float deltaH = targetH - smoothed[0];
        float deltaS = targetS - smoothed[1];
        float deltaV = targetV - smoothed[2];
        
        // Handle hue wrapping (shortest path around the color wheel)
        if (deltaH > 180) deltaH -= 360;
        if (deltaH < -180) deltaH += 360;
        
        // Apply rate limiting BEFORE smoothing
        // This ensures we never jump more than the max amount per frame
        deltaH = Math.max(-MAX_HUE_CHANGE, Math.min(MAX_HUE_CHANGE, deltaH));
        deltaS = Math.max(-MAX_SAT_CHANGE, Math.min(MAX_SAT_CHANGE, deltaS));
        deltaV = Math.max(-MAX_VAL_CHANGE, Math.min(MAX_VAL_CHANGE, deltaV));
        
        // Calculate rate-limited target
        float limitedTargetH = smoothed[0] + deltaH;
        float limitedTargetS = smoothed[1] + deltaS;
        float limitedTargetV = smoothed[2] + deltaV;
        
        // Apply exponential smoothing to the rate-limited values
        // This gives us smooth transitions that never jump too far
        smoothed[0] = (1 - smoothingFactor) * limitedTargetH + smoothingFactor * smoothed[0];
        smoothed[1] = (1 - smoothingFactor) * limitedTargetS + smoothingFactor * smoothed[1];
        smoothed[2] = (1 - smoothingFactor) * limitedTargetV + smoothingFactor * smoothed[2];
        
        // Keep hue in 0-360 range
        if (smoothed[0] < 0) smoothed[0] += 360;
        if (smoothed[0] >= 360) smoothed[0] -= 360;
        
        // Clamp saturation and value to valid ranges
        smoothed[1] = Math.max(0, Math.min(100, smoothed[1]));
        smoothed[2] = Math.max(0, Math.min(100, smoothed[2]));
        
        // Special handling for very low brightness to avoid jumps near black
        // When brightness is very low, reduce the importance of hue/saturation changes
        if (smoothed[2] < 5) {
            // Near black - heavily smooth hue and saturation to prevent jumps
            smoothed[0] = smoothed[0] * 0.9f + targetH * 0.1f;
            smoothed[1] = smoothed[1] * 0.9f + targetS * 0.1f;
        }
        
        // Convert smoothed HSV back to RGB
        int smoothedColor = LXColor.hsb(smoothed[0], smoothed[1], smoothed[2]);
        int r = (smoothedColor >> 16) & 0xFF;
        int g = (smoothedColor >> 8) & 0xFF;
        int b = smoothedColor & 0xFF;
        
        // Channel 1: Dimmer - ALWAYS 255 for full brightness
        output[offset] = (byte) 0xFF;
        
        // Channels 2-4: Smoothed RGB with gamma correction
        output[offset + 1] = gamma.red[r];
        output[offset + 2] = gamma.green[g];
        output[offset + 3] = gamma.blue[b];
        
        // Channels 5-7: Strobe, Function, Speed - set to 0
        output[offset + 4] = 0;  // Strobe off
        output[offset + 5] = 0;  // Function: manual control
        output[offset + 6] = 0;  // Speed: slowest
    }
    
    public void setSmoothingFactor(float factor) {
        this.smoothingFactor = Math.max(0.7f, Math.min(factor, 0.99f));
    }
    
    public float getSmoothingFactor() {
        return smoothingFactor;
    }
}