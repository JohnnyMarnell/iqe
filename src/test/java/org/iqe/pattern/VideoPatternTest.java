package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import org.junit.Before;
import org.junit.Test;
import org.junit.After;

import java.io.File;
import java.util.Arrays;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.Assert.*;

public class VideoPatternTest {
    
    private LX lx;
    private VideoPattern pattern;
    private volatile boolean loadingCompleted = false;
    
    @Before
    public void setUp() {
        // Create a minimal LX instance with a simple model
        LXModel model = new LXModel(Arrays.asList(createTestPoints()));
        lx = new LX(model);
    }
    
    @After
    public void tearDown() {
        if (pattern != null) {
            pattern.dispose();
        }
    }
    
    private LXPoint[] createTestPoints() {
        // Create a simple 10x10 grid of points at Y=700 (ceiling)
        LXPoint[] points = new LXPoint[100];
        int index = 0;
        for (int x = 0; x < 10; x++) {
            for (int z = 0; z < 10; z++) {
                points[index++] = new LXPoint(x * 10, 700, z * 10);
            }
        }
        return points;
    }
    
    @Test(timeout = 10000) // 10 second timeout
    public void testVideoLoadingDoesNotBlockMainThread() throws InterruptedException {
        System.out.println("Starting video loading test...");
        
        // Track if constructor blocks
        long startTime = System.currentTimeMillis();
        pattern = new VideoPattern(lx);
        pattern.setModel(lx.getModel()); // Initialize the model
        long constructorTime = System.currentTimeMillis() - startTime;
        
        System.out.println("Constructor completed in " + constructorTime + " ms");
        assertTrue("Constructor should complete quickly (< 500ms)", constructorTime < 500);
        
        // Simulate the render loop
        AtomicBoolean mainThreadBlocked = new AtomicBoolean(false);
        AtomicInteger runCount = new AtomicInteger(0);
        CountDownLatch loadingStarted = new CountDownLatch(1);
        CountDownLatch loadingFinished = new CountDownLatch(1);
        
        // Run pattern in simulated render loop
        Thread renderThread = new Thread(() -> {
            while (runCount.get() < 300 && !Thread.currentThread().isInterrupted()) { // Max 300 frames (~10 seconds at 30fps)
                long frameStart = System.currentTimeMillis();
                
                // Call run() to simulate render tick
                pattern.run(33.33); // ~30 fps
                
                long frameTime = System.currentTimeMillis() - frameStart;
                
                // Check if any frame takes too long (blocking)
                if (frameTime > 100) {
                    mainThreadBlocked.set(true);
                    System.err.println("Frame " + runCount.get() + " blocked for " + frameTime + " ms!");
                }
                
                // Check if loading started
                if (pattern.isLoading && loadingStarted.getCount() > 0) {
                    loadingStarted.countDown();
                    System.out.println("Loading started at frame " + runCount.get());
                }
                
                // Check if loading finished
                if (!pattern.frames.isEmpty() && loadingFinished.getCount() > 0) {
                    loadingFinished.countDown();
                    loadingCompleted = true;
                    System.out.println("Loading completed at frame " + runCount.get() + " with " + pattern.frames.size() + " frames");
                }
                
                // Once loading is done, run a few more frames to verify playback works
                if (loadingCompleted && runCount.get() > 100) {
                    break;
                }
                
                runCount.incrementAndGet();
                
                // Small delay to simulate frame timing
                try {
                    Thread.sleep(10);
                } catch (InterruptedException e) {
                    break;
                }
            }
        });
        
        renderThread.start();
        
        // Wait for loading to start
        assertTrue("Loading should start within 2 seconds", 
                   loadingStarted.await(2, TimeUnit.SECONDS));
        
        // Wait for loading to complete
        assertTrue("Loading should complete within 8 seconds", 
                   loadingFinished.await(8, TimeUnit.SECONDS));
        
        // Verify main thread was never blocked
        assertFalse("Main render thread should never be blocked", mainThreadBlocked.get());
        
        // Verify frames were loaded
        assertFalse("Frames should be loaded", pattern.frames.isEmpty());
        
        System.out.println("Test completed successfully. Loaded " + pattern.frames.size() + " frames");
        
        renderThread.interrupt();
        renderThread.join(1000);
    }
    
    @Test
    public void testVideoFileNotFound() throws InterruptedException {
        pattern = new VideoPattern(lx);
        pattern.setModel(lx.getModel());
        
        // Set a non-existent file
        pattern.videoPath.setValue("nonexistent.mp4");
        
        // Run a few frames
        for (int i = 0; i < 10; i++) {
            pattern.run(33.33);
            Thread.sleep(50);
        }
        
        // Wait a bit for loading attempt
        Thread.sleep(500);
        
        // Should handle gracefully
        assertTrue("Pattern should handle missing file gracefully", pattern.frames.isEmpty());
        assertFalse("Should not be loading after file not found", pattern.isLoading);
    }
    
    @Test
    public void testVideoPathChange() throws InterruptedException {
        pattern = new VideoPattern(lx);
        pattern.setModel(lx.getModel());
        
        // Create a test video file path
        File testVideo = new File("src/main/resources/videos/sample.webm");
        if (!testVideo.exists()) {
            System.out.println("Test video not found, skipping path change test");
            return;
        }
        
        // Initially set to non-existent
        pattern.videoPath.setValue("nonexistent.mp4");
        pattern.run(33.33);
        Thread.sleep(100);
        
        // Change to valid path
        pattern.videoPath.setValue(testVideo.getPath());
        
        // Run frames until loading starts
        for (int i = 0; i < 30; i++) {
            pattern.run(33.33);
            if (pattern.isLoading) {
                System.out.println("Loading started after path change");
                break;
            }
            Thread.sleep(50);
        }
        
        assertTrue("Should start loading after path change", pattern.isLoading);
    }
}