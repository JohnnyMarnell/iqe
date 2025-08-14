package org.iqe;

import heronarts.lx.output.LXBufferOutput;
import heronarts.lx.output.LXOutput;

/**
 * Custom ByteEncoder for 7-channel DMX ParCans
 * Outputs: Dimmer, R, G, B, Strobe, Function, Speed
 */
public class ParCanByteEncoder implements LXBufferOutput.ByteEncoder {
    
    // Always output 7 bytes per pixel
    private static final int NUM_BYTES = 7;
    
    @Override
    public int getNumBytes() {
        return NUM_BYTES;
    }
    
    @Override
    public void writeBytes(int color, LXOutput.GammaTable.Curve gamma, byte[] output, int offset) {
        // Extract RGB from color
        int r = (color >> 16) & 0xFF;
        int g = (color >> 8) & 0xFF;
        int b = color & 0xFF;
        
        // Channel 1: Dimmer - ALWAYS 255 for full brightness
        output[offset] = (byte) 0xFF;
        
        // Channels 2-4: RGB with gamma correction
        output[offset + 1] = gamma.red[r];
        output[offset + 2] = gamma.green[g];
        output[offset + 3] = gamma.blue[b];
        
        // Channels 5-7: Strobe, Function, Speed - set to 0
        output[offset + 4] = 0;  // Strobe off
        output[offset + 5] = 0;  // Function: manual control
        output[offset + 6] = 0;  // Speed: slowest
        
        // Debug log every 10th call to avoid spam
//        if (Math.random() < 0.01) {
//            LOG.info("ParCanByteEncoder writing at offset {}: Dimmer=255, R={}, G={}, B={}",
//                offset, r & 0xFF, g & 0xFF, b & 0xFF);
//        }
    }
}