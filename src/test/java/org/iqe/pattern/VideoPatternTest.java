package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Timeout;

import java.io.File;
import java.util.Arrays;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

public class VideoPatternTest {
    
    private LX lx;
    private VideoPattern pattern;
    private volatile boolean loadingCompleted = false;
    
    @BeforeEach
    public void setUp() {
        // Create a minimal LX instance with a simple model
        LXModel model = new LXModel(Arrays.asList(createTestPoints()));
        lx = new LX(model);
    }
    
    @AfterEach
    public void tearDown() {
        if (pattern != null) {
            pattern.dispose();
        }
    }
    
    private LXPoint[] createTestPoints() {
        // Create a simple 10x10 grid of points at Y=700 (ceiling)
        LXPoint[] points = new LXPoint[100];
        for (int i = 0; i < 100; i++) {
            int x = (i % 10) * 10;
            int z = (i / 10) * 10;
            points[i] = new LXPoint(x, 700, z);
            points[i].index = i;  // Ensure index matches array position
        }
        return points;
    }
    
    @Test
    @Timeout(value = 10, unit = TimeUnit.SECONDS)
    @DisplayName("Video loading should not block main thread")
    public void testVideoLoadingDoesNotBlockMainThread() throws InterruptedException {
        System.out.println("Starting video loading test...");
        
        // Track if constructor blocks
        long startTime = System.currentTimeMillis();
        pattern = new VideoPattern(lx);
        pattern.setModel(lx.getModel()); // Initialize the model
        long constructorTime = System.currentTimeMillis() - startTime;
        
        System.out.println("Constructor completed in " + constructorTime + " ms");
        assertTrue(constructorTime < 500, "Constructor should complete quickly (< 500ms)");
        
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
        assertTrue(loadingStarted.await(2, TimeUnit.SECONDS),
                   "Loading should start within 2 seconds");
        
        // Wait for loading to complete
        assertTrue(loadingFinished.await(8, TimeUnit.SECONDS),
                   "Loading should complete within 8 seconds");
        
        // Verify main thread was never blocked
        assertFalse(mainThreadBlocked.get(), "Main render thread should never be blocked");
        
        // Verify frames were loaded
        assertFalse(pattern.frames.isEmpty(), "Frames should be loaded");
        
        System.out.println("Test completed successfully. Loaded " + pattern.frames.size() + " frames");
        
        renderThread.interrupt();
        renderThread.join(1000);
    }
    
    @Test
    @DisplayName("Should handle missing video file gracefully")
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
        assertTrue(pattern.frames.isEmpty(), "Pattern should handle missing file gracefully");
        assertFalse(pattern.isLoading, "Should not be loading after file not found");
    }
    
    @Test
    @DisplayName("Should handle video path changes correctly")
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
        
        assertTrue(pattern.isLoading, "Should start loading after path change");
    }
}