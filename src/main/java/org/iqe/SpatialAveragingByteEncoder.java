package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.output.LXBufferOutput;
import heronarts.lx.output.LXOutput;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.HashMap;

/**
 * Byte encoder for DMX ParCans that averages colors from nearby pixels
 * to create a smoother, more coherent lighting effect.
 * 
 * Since we can't directly access the full color buffer from within the ByteEncoder,
 * this implementation stores colors as they pass through and uses them for spatial averaging.
 * This creates a frame of delay but provides smooth averaging across nearby pixels.
 */
public class SpatialAveragingByteEncoder implements LXBufferOutput.ByteEncoder {
    
    private LX lx;
    private float samplingRadius = 0.05f; // Default 5% of model points
    private Map<Integer, List<Integer>> nearbyPixelIndices; // Pre-computed neighbors for each fixture pixel
    private LXPoint[] fixturePoints;
    
    // Store the last frame's colors for averaging
    private int[] lastFrameColors;
    private boolean hasFrameData = false;
    
    public SpatialAveragingByteEncoder(LX lx, float initialRadius) {
        this.lx = lx;
        this.samplingRadius = initialRadius;
        this.nearbyPixelIndices = new HashMap<>();
    }
    
    /**
     * Pre-compute the nearest neighbors for each fixture pixel
     * @param fixturePoints The points in this fixture
     */
    public void precomputeNeighbors(LXPoint[] fixturePoints) {
        this.fixturePoints = fixturePoints;
        this.nearbyPixelIndices.clear();
        
        LXPoint[] allPoints = lx.getModel().points;
        int numNeighbors = Math.max(1, (int)(allPoints.length * samplingRadius));
        
        // Initialize color storage
        if (lastFrameColors == null || lastFrameColors.length != allPoints.length) {
            lastFrameColors = new int[allPoints.length];
        }
        
        LOG.info("SpatialAveragingByteEncoder: Computing {} neighbors for {} fixture pixels from {} total points", 
                 numNeighbors, fixturePoints.length, allPoints.length);
        
        for (int i = 0; i < fixturePoints.length; i++) {
            LXPoint fixturePoint = fixturePoints[i];
            
            // Create list of all points with their distances
            List<PointDistance> distances = new ArrayList<>();
            for (int j = 0; j < allPoints.length; j++) {
                LXPoint p = allPoints[j];
                float dist = distance(fixturePoint, p);
                distances.add(new PointDistance(j, dist));
            }
            
            // Sort by distance and take the N nearest
            distances.sort(Comparator.comparingDouble(pd -> pd.distance));
            List<Integer> neighbors = new ArrayList<>();
            for (int k = 0; k < Math.min(numNeighbors, distances.size()); k++) {
                neighbors.add(distances.get(k).index);
            }
            
            // Store neighbors for this fixture point
            nearbyPixelIndices.put(i, neighbors);
            
            if (i == 0) {
                // Log details for first pixel as example
                LOG.info("  Fixture pixel 0 at ({}, {}, {}) has {} neighbors", 
                        fixturePoint.x, fixturePoint.y, fixturePoint.z, neighbors.size());
                if (!neighbors.isEmpty()) {
                    LOG.info("  Nearest neighbor distance: {}, Farthest: {}", 
                            distances.get(0).distance, 
                            distances.get(Math.min(numNeighbors-1, distances.size()-1)).distance);
                }
            }
        }
    }
    
    /**
     * Update the sampling radius and recompute neighbors if needed
     */
    public void setSamplingRadius(float radius, LXPoint[] fixturePoints) {
        if (Math.abs(this.samplingRadius - radius) > 0.001f) {
            this.samplingRadius = radius;
            LOG.info("SpatialAveragingByteEncoder: Radius changed to {}%, recomputing neighbors", radius * 100);
            precomputeNeighbors(fixturePoints);
        }
    }
    
    /**
     * Store color data for a point (called from fixture during rendering)
     */
    public void updateColorData(int pointIndex, int color) {
        if (lastFrameColors != null && pointIndex >= 0 && pointIndex < lastFrameColors.length) {
            lastFrameColors[pointIndex] = color;
            hasFrameData = true;
        }
    }
    
    // Always output 7 bytes per pixel
    private static final int NUM_BYTES = 7;
    
    @Override
    public int getNumBytes() {
        return NUM_BYTES;
    }
    
    @Override
    public void writeBytes(int color, LXOutput.GammaTable.Curve gamma, byte[] output, int offset) {
        // Calculate which fixture pixel this is based on offset
        int pixelIndex = offset / NUM_BYTES;
        
        // Get the list of neighbor indices for this fixture pixel
        List<Integer> neighbors = nearbyPixelIndices.get(pixelIndex);
        
        // Store the current color for this fixture's point
        if (fixturePoints != null && pixelIndex < fixturePoints.length) {
            LXPoint fixturePoint = fixturePoints[pixelIndex];
            updateColorData(fixturePoint.index, color);
        }
        
        // If we don't have frame data yet or no neighbors, use direct color
        if (!hasFrameData || neighbors == null || neighbors.isEmpty()) {
            writeDirectColor(color, gamma, output, offset);
            return;
        }
        
        // Average the colors of all nearby pixels from last frame
        float totalR = 0, totalG = 0, totalB = 0;
        float totalWeight = 0;
        int validNeighbors = 0;
        
        for (int neighborIndex : neighbors) {
            if (neighborIndex >= 0 && neighborIndex < lastFrameColors.length) {
                int nColor = lastFrameColors[neighborIndex];
                
                // Skip if color is black/clear (not yet set)
                if (nColor == 0 || nColor == LXColor.CLEAR) {
                    continue;
                }
                
                float brightness = LXColor.luminosity(nColor);
                
                // Use brightness as weight so bright pixels have more influence
                // Add small epsilon to avoid zero weight
                float weight = brightness + 0.01f;
                
                totalR += weight * ((nColor >> 16) & 0xFF);
                totalG += weight * ((nColor >> 8) & 0xFF);
                totalB += weight * (nColor & 0xFF);
                totalWeight += weight;
                validNeighbors++;
            }
        }
        
        // Compute averaged color
        byte r, g, b;
        if (totalWeight > 0 && validNeighbors > 0) {
            // Use weighted average
            r = (byte) Math.min(255, Math.round(totalR / totalWeight));
            g = (byte) Math.min(255, Math.round(totalG / totalWeight));
            b = (byte) Math.min(255, Math.round(totalB / totalWeight));
        } else {
            // Fallback to current color if no valid neighbors
            r = (byte) ((color >> 16) & 0xFF);
            g = (byte) ((color >> 8) & 0xFF);
            b = (byte) (color & 0xFF);
        }
        
        // Apply gamma correction
        r = gamma.red[r & 0xFF];
        g = gamma.green[g & 0xFF];
        b = gamma.blue[b & 0xFF];
        
        // Write DMX channels: dimmer, R, G, B, amber, white, UV
        output[offset] = (byte) 0xFF;     // Dimmer always at full
        output[offset + 1] = r;           // Red
        output[offset + 2] = g;           // Green
        output[offset + 3] = b;           // Blue
        output[offset + 4] = 0;           // Amber (not used)
        output[offset + 5] = 0;           // White (not used)
        output[offset + 6] = 0;           // UV (not used)
    }
    
    private void writeDirectColor(int color, LXOutput.GammaTable.Curve gamma, byte[] output, int offset) {
        byte r = (byte) ((color >> 16) & 0xFF);
        byte g = (byte) ((color >> 8) & 0xFF);
        byte b = (byte) (color & 0xFF);
        
        // Apply gamma correction
        r = gamma.red[r & 0xFF];
        g = gamma.green[g & 0xFF];
        b = gamma.blue[b & 0xFF];
        
        output[offset] = (byte) 0xFF;     // Dimmer
        output[offset + 1] = r;
        output[offset + 2] = g;
        output[offset + 3] = b;
        output[offset + 4] = 0;
        output[offset + 5] = 0;
        output[offset + 6] = 0;
    }
    
    private float distance(LXPoint p1, LXPoint p2) {
        float dx = p1.x - p2.x;
        float dy = p1.y - p2.y;
        float dz = p1.z - p2.z;
        return (float) Math.sqrt(dx*dx + dy*dy + dz*dz);
    }
    
    private static class PointDistance {
        final int index;
        final float distance;
        
        PointDistance(int index, float distance) {
            this.index = index;
            this.distance = distance;
        }
    }
}