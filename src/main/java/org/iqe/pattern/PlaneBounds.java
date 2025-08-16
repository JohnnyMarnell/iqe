package org.iqe.pattern;

import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import org.iqe.LOG;

import java.util.HashMap;
import java.util.Map;

/**
 * Utility class for calculating and caching bounds of the plane with the most pixels.
 * Shared between ImagePattern, VideoPattern, and other patterns that need to render on a 2D plane.
 */
public class PlaneBounds {
    
    public final double minX;
    public final double maxX;
    public final double minZ;
    public final double maxZ;
    public final double targetY;
    public final int pixelCount;
    
    // Static cache to store bounds per model instance
    private static final Map<Integer, PlaneBounds> boundsCache = new HashMap<>();
    
    private PlaneBounds(double minX, double maxX, double minZ, double maxZ, double targetY, int pixelCount) {
        this.minX = minX;
        this.maxX = maxX;
        this.minZ = minZ;
        this.maxZ = maxZ;
        this.targetY = targetY;
        this.pixelCount = pixelCount;
    }
    
    /**
     * Get or calculate the bounds for the plane with the most pixels.
     * Results are cached per model instance.
     */
    public static PlaneBounds getBounds(LXModel model) {
        // Use model's identity hash code as cache key
        int modelKey = System.identityHashCode(model);
        
        // Check if already calculated for this model
        PlaneBounds cached = boundsCache.get(modelKey);
        if (cached != null) {
            return cached;
        }
        
        // Calculate bounds for the plane with the most pixels
        PlaneBounds bounds = calculateBounds(model);
        boundsCache.put(modelKey, bounds);
        
        return bounds;
    }
    
    /**
     * Clear the cache if model changes (rarely needed)
     */
    public static void clearCache() {
        boundsCache.clear();
    }
    
    private static PlaneBounds calculateBounds(LXModel model) {
        // Group pixels by Y coordinate (with small tolerance for same plane)
        Map<Integer, Integer> yPlaneCounts = new HashMap<>();
        Map<Integer, Double> yPlaneActualY = new HashMap<>();
        double tolerance = 10.0; // Tolerance for grouping pixels in same plane
        
        // Count pixels at each Y level
        for (LXModel child : model.children) {
            for (LXPoint p : child.points) {
                // Round Y to nearest tolerance value to group similar heights
                int yBucket = (int) Math.round(p.y / tolerance);
                yPlaneCounts.merge(yBucket, 1, Integer::sum);
                
                // Store the actual Y value for this bucket (use max)
                yPlaneActualY.merge(yBucket, (double) p.y, Math::max);
            }
        }
        
        // Find the Y plane with the most pixels
        int maxCount = 0;
        int selectedBucket = 0;
        for (Map.Entry<Integer, Integer> entry : yPlaneCounts.entrySet()) {
            if (entry.getValue() > maxCount) {
                maxCount = entry.getValue();
                selectedBucket = entry.getKey();
            }
        }
        
        // Get the actual Y value for the selected plane
        double targetY = yPlaneActualY.getOrDefault(selectedBucket, 0.0);
        double threshold = targetY - tolerance / 2;
        double upperThreshold = targetY + tolerance / 2;
        
        // Calculate bounds only for pixels in the selected plane
        double minX = Double.MAX_VALUE;
        double maxX = Double.MIN_VALUE;
        double minZ = Double.MAX_VALUE;
        double maxZ = Double.MIN_VALUE;
        int actualPixelCount = 0;
        
        for (LXModel child : model.children) {
            for (LXPoint p : child.points) {
                if (p.y >= threshold && p.y <= upperThreshold) {
                    minX = Math.min(minX, p.x);
                    maxX = Math.max(maxX, p.x);
                    minZ = Math.min(minZ, p.z);
                    maxZ = Math.max(maxZ, p.z);
                    actualPixelCount++;
                }
            }
        }
        
        PlaneBounds bounds = new PlaneBounds(minX, maxX, minZ, maxZ, targetY, actualPixelCount);
        
        LOG.info("PlaneBounds calculated: X[{}, {}], Z[{}, {}], Y: {} (±{}), {} pixels", 
                 minX, maxX, minZ, maxZ, targetY, tolerance/2, actualPixelCount);
        
        return bounds;
    }
    
    /**
     * Check if a point is within the selected plane (with tolerance)
     */
    public boolean isInPlane(LXPoint p, double tolerance) {
        return Math.abs(p.y - targetY) <= tolerance;
    }
    
    /**
     * Check if a point is within the selected plane (default tolerance of 10)
     */
    public boolean isInPlane(LXPoint p) {
        return isInPlane(p, 10.0);
    }
}