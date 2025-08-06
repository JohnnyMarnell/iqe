package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Timeout;

import java.util.Arrays;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

public class VideoPatternAsyncTest {
    
    @Test
    @DisplayName("Video loading should be completely asynchronous")
    @Timeout(value = 15, unit = TimeUnit.SECONDS)
    public void testVideoLoadingIsAsync() throws InterruptedException {
        System.out.println("=== Testing VideoPattern Async Loading ===");
        
        // Create simple model and LX
        LXPoint[] points = new LXPoint[100];
        for (int i = 0; i < 100; i++) {
            points[i] = new LXPoint(i * 10, 700, 0);
            points[i].index = i;  // Ensure index matches array position
        }
        LXModel model = new LXModel(Arrays.asList(points));
        LX lx = new LX(model);
        
        // Create pattern - should not block
        long startTime = System.currentTimeMillis();
        VideoPattern pattern = new VideoPattern(lx);
        pattern.setModel(model);
        long constructorTime = System.currentTimeMillis() - startTime;
        
        System.out.println("Constructor time: " + constructorTime + "ms");
        assertTrue(constructorTime < 100, "Constructor must be fast (<100ms)");
        
        // First run triggers loading
        startTime = System.currentTimeMillis();
        pattern.run(33.33);
        long firstRunTime = System.currentTimeMillis() - startTime;
        
        System.out.println("First run time: " + firstRunTime + "ms");
        assertTrue(firstRunTime < 100, "First run must not block (<100ms)");
        
        // Verify loading started
        Thread.sleep(100);
        assertTrue(pattern.isLoading, "Loading should have started");
        
        // Run frames while loading - should not block
        System.out.println("Running frames while loading...");
        for (int i = 0; i < 10; i++) {
            startTime = System.currentTimeMillis();
            pattern.run(33.33);
            long frameTime = System.currentTimeMillis() - startTime;
            
            System.out.println("Frame " + i + " time: " + frameTime + "ms");
            assertTrue(frameTime < 50, "Frame " + i + " must not block (<50ms)");
            Thread.sleep(50);
        }
        
        // Wait for loading to complete
        System.out.println("Waiting for loading to complete...");
        int maxWaitIterations = 100; // 10 seconds max
        while (pattern.isLoading && maxWaitIterations-- > 0) {
            Thread.sleep(100);
        }
        
        assertFalse(pattern.isLoading, "Loading should complete");
        assertFalse(pattern.frames.isEmpty(), "Frames should be loaded");
        System.out.println("Loading completed with " + pattern.frames.size() + " frames");
        
        // Verify pattern can run after loading
        startTime = System.currentTimeMillis();
        pattern.run(33.33);
        long postLoadRunTime = System.currentTimeMillis() - startTime;
        System.out.println("Post-load run time: " + postLoadRunTime + "ms");
        assertTrue(postLoadRunTime < 50, "Post-load run must be fast (<50ms)");
        
        pattern.dispose();
        System.out.println("=== Test Passed ===");
    }
}