package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import org.junit.Test;

import java.util.Arrays;

import static org.junit.Assert.*;

public class VideoPatternAsyncTest {
    
    @Test
    public void testVideoLoadingIsAsync() throws InterruptedException {
        System.out.println("=== Testing VideoPattern Async Loading ===");
        
        // Create simple model and LX
        LXPoint[] points = new LXPoint[100];
        for (int i = 0; i < 100; i++) {
            points[i] = new LXPoint(i * 10, 700, 0);
        }
        LXModel model = new LXModel(Arrays.asList(points));
        LX lx = new LX(model);
        
        // Create pattern - should not block
        long startTime = System.currentTimeMillis();
        VideoPattern pattern = new VideoPattern(lx);
        pattern.setModel(model);
        long constructorTime = System.currentTimeMillis() - startTime;
        
        System.out.println("Constructor time: " + constructorTime + "ms");
        assertTrue("Constructor must be fast (<100ms)", constructorTime < 100);
        
        // First run triggers loading
        startTime = System.currentTimeMillis();
        pattern.run(33.33);
        long firstRunTime = System.currentTimeMillis() - startTime;
        
        System.out.println("First run time: " + firstRunTime + "ms");
        assertTrue("First run must not block (<100ms)", firstRunTime < 100);
        
        // Verify loading started
        Thread.sleep(100);
        assertTrue("Loading should have started", pattern.isLoading);
        
        // Run frames while loading - should not block
        System.out.println("Running frames while loading...");
        for (int i = 0; i < 10; i++) {
            startTime = System.currentTimeMillis();
            pattern.run(33.33);
            long frameTime = System.currentTimeMillis() - startTime;
            
            System.out.println("Frame " + i + " time: " + frameTime + "ms");
            assertTrue("Frame " + i + " must not block (<50ms)", frameTime < 50);
            Thread.sleep(50);
        }
        
        // Wait for loading to complete
        System.out.println("Waiting for loading to complete...");
        int maxWaitIterations = 100; // 10 seconds max
        while (pattern.isLoading && maxWaitIterations-- > 0) {
            Thread.sleep(100);
        }
        
        assertFalse("Loading should complete", pattern.isLoading);
        assertFalse("Frames should be loaded", pattern.frames.isEmpty());
        System.out.println("Loading completed with " + pattern.frames.size() + " frames");
        
        // Verify pattern can run after loading
        startTime = System.currentTimeMillis();
        pattern.run(33.33);
        long postLoadRunTime = System.currentTimeMillis() - startTime;
        System.out.println("Post-load run time: " + postLoadRunTime + "ms");
        assertTrue("Post-load run must be fast (<50ms)", postLoadRunTime < 50);
        
        pattern.dispose();
        System.out.println("=== Test Passed ===");
    }
}