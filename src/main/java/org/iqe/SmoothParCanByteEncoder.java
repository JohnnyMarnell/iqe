package org.iqe;

import heronarts.lx.output.LXBufferOutput;
import heronarts.lx.output.LXOutput;
import java.util.HashMap;
import java.util.Map;

/**
 * Smoothed ByteEncoder for 7-channel DMX ParCans
 * Uses exponential smoothing to create fluid transitions
 * Prevents jumpy/strobe-like effects on spot lights
 */
public class SmoothParCanByteEncoder implements LXBufferOutput.ByteEncoder {
    
    // Always output 7 bytes per pixel
    private static final int NUM_BYTES = 7;
    
    // Smoothing factor (0 = no smoothing, 1 = infinite smoothing)
    // Start with moderate smoothing - can be tuned
    private float smoothingFactor = 0.85f;
    
    // Store smoothed RGB values per offset (for multiple ParCans)
    private Map<Integer, float[]> smoothedValues = new HashMap<>();
    
    // Minimum change threshold - ignore tiny changes to reduce flicker
    private static final float THRESHOLD = 2.0f;
    
    public SmoothParCanByteEncoder() {
        this(0.85f);
    }
    
    public SmoothParCanByteEncoder(float smoothingFactor) {
        this.smoothingFactor = Math.max(0, Math.min(smoothingFactor, 0.99f));
    }
    
    @Override
    public int getNumBytes() {
        return NUM_BYTES;
    }
    
    @Override
    public void writeBytes(int color, LXOutput.GammaTable.Curve gamma, byte[] output, int offset) {
        // Extract target RGB from color
        float targetR = (color >> 16) & 0xFF;
        float targetG = (color >> 8) & 0xFF;
        float targetB = color & 0xFF;
        
        // Get or initialize smoothed values for this offset
        float[] smoothed = smoothedValues.computeIfAbsent(offset, k -> new float[]{targetR, targetG, targetB});
        
        // Apply exponential smoothing
        // New = (1-α) * Target + α * Previous
        // Higher α = more smoothing, slower response
        smoothed[0] = (1 - smoothingFactor) * targetR + smoothingFactor * smoothed[0];
        smoothed[1] = (1 - smoothingFactor) * targetG + smoothingFactor * smoothed[1];
        smoothed[2] = (1 - smoothingFactor) * targetB + smoothingFactor * smoothed[2];
        
        // Apply threshold to reduce tiny flickers
        if (Math.abs(smoothed[0] - targetR) < THRESHOLD) smoothed[0] = targetR;
        if (Math.abs(smoothed[1] - targetG) < THRESHOLD) smoothed[1] = targetG;
        if (Math.abs(smoothed[2] - targetB) < THRESHOLD) smoothed[2] = targetB;
        
        // Convert to bytes with gamma correction
        int r = Math.round(smoothed[0]);
        int g = Math.round(smoothed[1]);
        int b = Math.round(smoothed[2]);
        
        // Clamp to valid range
        r = Math.max(0, Math.min(255, r));
        g = Math.max(0, Math.min(255, g));
        b = Math.max(0, Math.min(255, b));
        
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
        this.smoothingFactor = Math.max(0, Math.min(factor, 0.99f));
    }
    
    public float getSmoothingFactor() {
        return smoothingFactor;
    }
}