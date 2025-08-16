package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import heronarts.lx.parameter.BooleanParameter;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.StringParameter;
import heronarts.lx.pattern.LXPattern;
import org.iqe.LOG;

import javax.imageio.ImageIO;
import java.awt.*;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.bytedeco.javacv.*;

@LXCategory(LXCategory.TEST)
public class VideoPattern extends LXPattern {
    
    private static final int MAX_RESAMPLED_WIDTH = 420;
    private static final int MAX_RESAMPLED_HEIGHT = 240;
    private static final int MAX_FRAMES_IN_MEMORY = 10000;  // Allow up to 10K frames (~83 seconds at 120fps)
    private static final int FRAME_LOAD_BATCH_SIZE = 10;
    private static final int BUFFER_POOL_SIZE = 4;  // Number of pre-allocated buffers
    
    // Static memory pool shared across all VideoPattern instances
    private static class FrameBufferPool {
        private final int[][][][] buffers = new int[BUFFER_POOL_SIZE][][][];
        private final AtomicInteger currentBufferIndex = new AtomicInteger(0);
        private final boolean[] bufferInUse = new boolean[BUFFER_POOL_SIZE];
        
        synchronized int[][][] acquireBuffer(int frameCount, int height, int width) {
            // Find next available buffer
            for (int i = 0; i < BUFFER_POOL_SIZE; i++) {
                int index = (currentBufferIndex.get() + i) % BUFFER_POOL_SIZE;
                if (!bufferInUse[index]) {
                    // Allocate or resize if needed
                    if (buffers[index] == null || 
                        buffers[index].length < frameCount ||
                        (buffers[index].length > 0 && 
                         (buffers[index][0].length != height || 
                          buffers[index][0][0].length != width))) {
                        LOG.info("Allocating new buffer {} for {} frames at {}x{}", 
                                index, frameCount, width, height);
                        buffers[index] = new int[frameCount][height][width];
                    }
                    bufferInUse[index] = true;
                    currentBufferIndex.set((index + 1) % BUFFER_POOL_SIZE);
                    return buffers[index];
                }
            }
            // All buffers in use, force allocate new one (shouldn't happen with 4 buffers)
            LOG.error("All {} buffers in use, forcing allocation", BUFFER_POOL_SIZE);
            return new int[frameCount][height][width];
        }
        
        synchronized void releaseBuffer(int[][][] buffer) {
            if (buffer == null) return;
            for (int i = 0; i < BUFFER_POOL_SIZE; i++) {
                if (buffers[i] == buffer) {
                    bufferInUse[i] = false;
                    LOG.info("Released buffer {}", i);
                    return;
                }
            }
        }
    }
    
    private static final FrameBufferPool bufferPool = new FrameBufferPool();
    
    public final StringParameter videoPath = new StringParameter("videoPath", "src/main/resources/videos/sample2-24p-120fps.mp4")
        .setDescription("Path to the video file");
    
    private final CompoundParameter playbackSpeed = new CompoundParameter("speed", 1.0, 0.1, 4.0)
        .setDescription("Playback speed multiplier");
    
    private final BooleanParameter loop = new BooleanParameter("loop", true)
        .setDescription("Loop the video");
    
    private final BooleanParameter pingPong = new BooleanParameter("pingPong", true)
        .setDescription("Play forward then backward (ping-pong mode)");
    
    private final BooleanParameter playing = new BooleanParameter("playing", true)
        .setDescription("Play/Pause");
    
    private final CompoundParameter scale = new CompoundParameter("scale", 1.0, 0.1, 5.0)
        .setDescription("Scale factor for the video");
    
    private final CompoundParameter xOffset = new CompoundParameter("xOffset", 0, -1, 1)
        .setDescription("Horizontal offset");
    
    private final CompoundParameter yOffset = new CompoundParameter("yOffset", 0, -1, 1)
        .setDescription("Vertical offset");
    
    private final CompoundParameter brightness = new CompoundParameter("brightness", 1.0, 0, 2.0)
        .setDescription("Brightness adjustment");
    
    private final BooleanParameter preserveAspect = new BooleanParameter("preserveAspect", false)
        .setDescription("Preserve video aspect ratio");
    
    private final BooleanParameter interpolate = new BooleanParameter("interpolate", true)
        .setDescription("Interpolate frames for smooth slow-motion");
    
    private ExecutorService loadingExecutor = null;
    
    private ExecutorService getLoadingExecutor() {
        if (loadingExecutor == null) {
            loadingExecutor = Executors.newSingleThreadExecutor(r -> {
                Thread t = new Thread(r, "VideoPattern-Loader");
                t.setDaemon(true);
                return t;
            });
        }
        return loadingExecutor;
    }
    
    final AtomicReference<int[][][]> framePixels = new AtomicReference<>(null); // [frame][y][x] = ARGB int
    final AtomicInteger numFrames = new AtomicInteger(0);
    final AtomicBoolean isLoading = new AtomicBoolean(false);
    private final AtomicReference<String> loadingStatus = new AtomicReference<>("");
    private final AtomicReference<String> currentVideoPath = new AtomicReference<>("");
    private final AtomicInteger currentFrameIndex = new AtomicInteger(0);
    private double frameAccumulator = 0;
    private double fps = 30.0;
    private int resampledWidth = MAX_RESAMPLED_WIDTH;
    private int resampledHeight = MAX_RESAMPLED_HEIGHT;
    private int playbackDirection = 1; // 1 for forward, -1 for backward
    
    private Future<?> currentLoadTask = null;
    private boolean hasLoggedEmpty = false;
    private boolean hasLoggedLoading = false;
    
    // Cached bounds for the plane with most pixels
    private PlaneBounds bounds = null;
    
    public VideoPattern(LX lx) {
        super(lx);
        LOG.info("VideoPattern constructor starting");
        addParameter(videoPath);
        addParameter(playbackSpeed);
        addParameter(loop);
        addParameter(pingPong);
        addParameter(playing);
        addParameter(scale);
        addParameter(xOffset);
        addParameter(yOffset);
        addParameter(brightness);
        addParameter(preserveAspect);
        addParameter(interpolate);
        
        // Don't load in constructor - let run() trigger it
        LOG.info("VideoPattern constructor completed, video will load on first run");
    }
    
    @Override
    protected void onActive() {
        super.onActive();
        LOG.info("VideoPattern onActive - pattern is being transitioned into");
        
        // Load the video when pattern becomes active
        String path = videoPath.getString();
        if (!path.isEmpty() && !path.equals(currentVideoPath.get())) {
            LOG.info("Loading video on activation: {}", path);
            currentVideoPath.set(path);
            loadVideoAsync(path);
        }
    }
    
    @Override
    protected void onInactive() {
        super.onInactive();
        LOG.info("VideoPattern onInactive - pattern is being transitioned out, releasing buffer");
        
        // Cancel any ongoing load
        if (currentLoadTask != null) {
            currentLoadTask.cancel(true);
            currentLoadTask = null;
        }
        
        // Release the buffer back to the pool
        int[][][] currentBuffer = framePixels.getAndSet(null);
        if (currentBuffer != null) {
            bufferPool.releaseBuffer(currentBuffer);
        }
        numFrames.set(0);
        currentFrameIndex.set(0);
        frameAccumulator = 0;
        playbackDirection = 1; // Reset to forward
        
        // Clear the current path so it reloads when reactivated
        currentVideoPath.set("");
        
        LOG.info("VideoPattern buffer released");
    }
    
    
    private void loadVideoAsync(String path) {
        LOG.info("loadVideoAsync called for path: {}", path);
        if (!isLoading.compareAndSet(false, true)) {
            LOG.info("Video is already loading, skipping new load request");
            return;
        }
        
        if (currentLoadTask != null && !currentLoadTask.isDone()) {
            LOG.info("Cancelling previous load task");
            currentLoadTask.cancel(true);
        }
        
        loadingStatus.set("Loading...");
        LOG.info("Starting background load task for: {}", path);
        
        currentLoadTask = getLoadingExecutor().submit(() -> {
            LOG.info("Background thread started for loading: {}", path);
            long startTime = System.currentTimeMillis();
            try {
                loadVideoInBackground(path);
                long duration = System.currentTimeMillis() - startTime;
                LOG.info("Video loading completed in {} ms", duration);
            } catch (Exception e) {
                LOG.error("Failed to load video in background: {}", e.getMessage(), e);
                loadingStatus.set("Error: " + e.getMessage());
            } finally {
                isLoading.set(false);
                LOG.info("Background loading thread finished");
            }
        });
        LOG.info("loadVideoAsync submitted task, returning to main thread");
    }
    
    private void loadVideoInBackground(String path) {
        LOG.info("loadVideoInBackground started on thread: {}", Thread.currentThread().getName());
        File file = new File(path);
        if (!file.exists()) {
            LOG.error("Video file not found: {}", path);
            loadingStatus.set("File not found");
            return;
        }
        
        LOG.info("Video file exists: {} (size: {} bytes)", file.getAbsolutePath(), file.length());
        
        FFmpegFrameGrabber grabber = null;
        Java2DFrameConverter converter = new Java2DFrameConverter();
        List<int[][]> tempFramePixels = new ArrayList<>(); // Temporary list to collect frames
        
        try {
            loadingStatus.set("Opening video...");
            LOG.info("Creating FFmpegFrameGrabber for: {}", file.getAbsolutePath());
            grabber = new FFmpegFrameGrabber(file);
            
            LOG.info("Starting grabber...");
            long grabberStartTime = System.currentTimeMillis();
            grabber.start();
            LOG.info("Grabber started in {} ms", System.currentTimeMillis() - grabberStartTime);
            
            double videoFps = grabber.getFrameRate();
            if (videoFps <= 0) videoFps = 30.0;
            
            int originalWidth = grabber.getImageWidth();
            int originalHeight = grabber.getImageHeight();
            int totalFrames = grabber.getLengthInFrames();
            
            LOG.info("Opening video: {} ({}x{}, {} fps, {} frames)", 
                     path, originalWidth, originalHeight, videoFps, totalFrames);
            
            // For high frame rate videos, we might want to skip frames when loading
            // to avoid using too much memory
            if (videoFps > 60 && totalFrames > MAX_FRAMES_IN_MEMORY) {
                LOG.info("High frame rate video detected ({}fps), will adjust frame loading", videoFps);
            }
            
            double aspectRatio = (double) originalWidth / originalHeight;
            int targetWidth, targetHeight;
            
            if (originalWidth > MAX_RESAMPLED_WIDTH || originalHeight > MAX_RESAMPLED_HEIGHT) {
                if (aspectRatio > (double) MAX_RESAMPLED_WIDTH / MAX_RESAMPLED_HEIGHT) {
                    targetWidth = MAX_RESAMPLED_WIDTH;
                    targetHeight = (int) (MAX_RESAMPLED_WIDTH / aspectRatio);
                } else {
                    targetHeight = MAX_RESAMPLED_HEIGHT;
                    targetWidth = (int) (MAX_RESAMPLED_HEIGHT * aspectRatio);
                }
                LOG.info("Resampling video from {}x{} to {}x{}", 
                         originalWidth, originalHeight, targetWidth, targetHeight);
            } else {
                targetWidth = originalWidth;
                targetHeight = originalHeight;
                LOG.info("Using original video dimensions: {}x{}", targetWidth, targetHeight);
            }
            
            // Load all frames up to our memory limit
            int framesToLoad = Math.min(totalFrames, MAX_FRAMES_IN_MEMORY);
            int frameSkip = totalFrames > MAX_FRAMES_IN_MEMORY ? totalFrames / MAX_FRAMES_IN_MEMORY : 1;
            
            LOG.info("Planning to load {} frames (skip every {} frames) from total of {} frames", 
                     framesToLoad, frameSkip, totalFrames);
            
            if (totalFrames > MAX_FRAMES_IN_MEMORY) {
                LOG.info("WARNING: Video has {} frames but we can only load {} in memory. Consider increasing MAX_FRAMES_IN_MEMORY", 
                         totalFrames, MAX_FRAMES_IN_MEMORY);
            }
            
            org.bytedeco.javacv.Frame frame;
            int frameCount = 0;
            int loadedFrames = 0;
            long frameLoadStartTime = System.currentTimeMillis();
            
            LOG.info("Starting frame grab loop...");
            while ((frame = grabber.grab()) != null && loadedFrames < framesToLoad) {
                if (Thread.currentThread().isInterrupted()) {
                    LOG.info("Video loading interrupted at frame {}", frameCount);
                    break;
                }
                
                if (frame.image != null && frameCount % frameSkip == 0) {
                    long frameProcessStart = System.currentTimeMillis();
                    BufferedImage originalImage = converter.convert(frame);
                    
                    if (originalImage != null) {
                        // Only log first frame details and every 10th frame
                        if (loadedFrames == 0 || loadedFrames % 10 == 0) {
                            LOG.info("Processing frame {} ({}x{}) -> resampling to {}x{}", 
                                    frameCount, originalImage.getWidth(), originalImage.getHeight(),
                                    targetWidth, targetHeight);
                        }
                        BufferedImage resampledImage = resampleImage(originalImage, targetWidth, targetHeight);
                        
                        // Convert BufferedImage to int array
                        int[][] pixelData = new int[targetHeight][targetWidth];
                        for (int y = 0; y < targetHeight; y++) {
                            for (int x = 0; x < targetWidth; x++) {
                                pixelData[y][x] = resampledImage.getRGB(x, y);
                            }
                        }
                        tempFramePixels.add(pixelData);
                        loadedFrames++;
                        
                        long frameProcessTime = System.currentTimeMillis() - frameProcessStart;
                        if (loadedFrames % FRAME_LOAD_BATCH_SIZE == 0) {
                            loadingStatus.set(String.format("Loading... %d/%d frames", loadedFrames, framesToLoad));
                            long avgTimePerFrame = (System.currentTimeMillis() - frameLoadStartTime) / loadedFrames;
                            LOG.info("Progress: {} frames loaded (last frame: {} ms, avg: {} ms/frame, total elapsed: {} ms)", 
                                    loadedFrames, frameProcessTime, avgTimePerFrame, 
                                    System.currentTimeMillis() - frameLoadStartTime);
                        }
                    }
                }
                frameCount++;
            }
            LOG.info("Frame grab loop completed. Loaded {} frames in {} ms", 
                     loadedFrames, System.currentTimeMillis() - frameLoadStartTime);
            
            LOG.info("Updating frame buffer with {} new frames", tempFramePixels.size());
            // Acquire a buffer from the pool and copy frames into it
            if (tempFramePixels.size() > 0 && targetHeight > 0 && targetWidth > 0) {
                int[][][] newFramePixels = bufferPool.acquireBuffer(
                    tempFramePixels.size(), targetHeight, targetWidth);
                
                // Copy frames into the pre-allocated buffer
                for (int i = 0; i < tempFramePixels.size(); i++) {
                    int[][] sourceFrame = tempFramePixels.get(i);
                    int[][] destFrame = newFramePixels[i];
                    for (int y = 0; y < targetHeight; y++) {
                        System.arraycopy(sourceFrame[y], 0, destFrame[y], 0, targetWidth);
                    }
                }
                
                // Release old buffer if exists
                int[][][] oldBuffer = framePixels.getAndSet(newFramePixels);
                if (oldBuffer != null) {
                    bufferPool.releaseBuffer(oldBuffer);
                }
                numFrames.set(tempFramePixels.size());
            } else {
                LOG.error("No frames to load or invalid dimensions");
                framePixels.set(null);
                numFrames.set(0);
            }
            fps = videoFps;
            resampledWidth = targetWidth;
            resampledHeight = targetHeight;
            currentFrameIndex.set(0);
            frameAccumulator = 0;
            playbackDirection = 1; // Reset to forward when loading new video
            
            loadingStatus.set("");
            LOG.info("Successfully loaded {} frames from video (resampled to {}x{})", 
                     numFrames, targetWidth, targetHeight);
            
        } catch (FrameGrabber.Exception e) {
            LOG.error("Error loading video: {}", e.getMessage(), e);
            loadingStatus.set("Error: " + e.getMessage());
            // Release any existing buffer on error
            int[][][] existingBuffer = framePixels.getAndSet(null);
            if (existingBuffer != null) {
                bufferPool.releaseBuffer(existingBuffer);
            }
            numFrames.set(0);
        } catch (Exception e) {
            LOG.error("Unexpected error loading video: {}", e.getMessage(), e);
            loadingStatus.set("Error: " + e.getMessage());
            // Release any existing buffer on error
            int[][][] existingBuffer = framePixels.getAndSet(null);
            if (existingBuffer != null) {
                bufferPool.releaseBuffer(existingBuffer);
            }
            numFrames.set(0);
        } finally {
            if (grabber != null) {
                try {
                    LOG.info("Stopping and releasing grabber...");
                    long stopTime = System.currentTimeMillis();
                    grabber.stop();
                    grabber.release();
                    LOG.info("Grabber stopped and released in {} ms", System.currentTimeMillis() - stopTime);
                } catch (Exception e) {
                    LOG.error("Error closing grabber: {}", e.getMessage());
                }
            }
        }
    }
    
    private BufferedImage resampleImage(BufferedImage original, int targetWidth, int targetHeight) {
        if (original.getWidth() == targetWidth && original.getHeight() == targetHeight) {
            return original;
        }
        
        BufferedImage resampled = new BufferedImage(targetWidth, targetHeight, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = resampled.createGraphics();
        g.setRenderingHint(RenderingHints.KEY_INTERPOLATION, RenderingHints.VALUE_INTERPOLATION_BILINEAR);
        g.setRenderingHint(RenderingHints.KEY_RENDERING, RenderingHints.VALUE_RENDER_QUALITY);
        g.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON);
        g.drawImage(original, 0, 0, targetWidth, targetHeight, null);
        g.dispose();
        
        return resampled;
    }

    @Override
    protected void run(double deltaMs) {
        String newPath = videoPath.getString();
        if (!newPath.equals(currentVideoPath.get())) {
            LOG.info("Video path changed from '{}' to '{}'", currentVideoPath.get(), newPath);
            currentVideoPath.set(newPath);
            loadVideoAsync(newPath);
        }

        // Get bounds if needed (calculated only once per model)
        if (bounds == null) {
            bounds = PlaneBounds.getBounds(model);
        }

        for (LXPoint p : model.points) {
            colors[p.index] = LXColor.CLEAR;
        }

        int[][][] currentFrames = framePixels.get();
        int frameCount = numFrames.get();
        
        if (currentFrames == null || frameCount == 0) {
            if (isLoading.get()) {
                if (!hasLoggedLoading) {
                    LOG.info("Frames empty, loading in progress: {}", loadingStatus.get());
                    hasLoggedLoading = true;
                    hasLoggedEmpty = false;
                }
            } else {
                if (!hasLoggedEmpty) {
                    LOG.info("Frames empty, not loading");
                    hasLoggedEmpty = true;
                    hasLoggedLoading = false;
                }
            }
            return;
        }

        // Reset logging flags when we have frames
        if (hasLoggedEmpty || hasLoggedLoading) {
            LOG.info("Frames loaded, starting playback");
            hasLoggedEmpty = false;
            hasLoggedLoading = false;
        }
        
        int frameWidth = resampledWidth;
        int frameHeight = resampledHeight;
        
        if (playing.isOn() && !isLoading.get()) {
            // Calculate how many video frames should advance based on real time
            // deltaMs is the real time passed, fps is the video's frame rate
            // We want to advance (deltaMs/1000) * fps frames to maintain proper playback speed
            double secondsElapsed = deltaMs / 1000.0;
            double framesToAdvance = secondsElapsed * fps * playbackSpeed.getValue();
            frameAccumulator += framesToAdvance;
            
            // Debug logging for frame advancement
            if (currentFrameIndex.get() == 0 && frameAccumulator < 1.0) {
                LOG.info("Frame animation debug: deltaMs={}, fps={}, speed={}, framesToAdvance={}, accumulator={}", 
                        deltaMs, fps, playbackSpeed.getValue(), framesToAdvance, frameAccumulator);
            }
            
            while (frameAccumulator >= 1.0) {
                frameAccumulator -= 1.0;
                int oldIndex = currentFrameIndex.get();
                int newIndex = oldIndex + playbackDirection;
                
                // Handle boundaries based on mode
                if (pingPong.isOn()) {
                    // Ping-pong mode: reverse direction at boundaries
                    if (newIndex >= frameCount) {
                        playbackDirection = -1;
                        newIndex = frameCount - 2; // Start going backward from second-to-last frame
                        if (newIndex < 0) newIndex = 0;
                        LOG.info("Reversing video playback direction (backward)");
                    } else if (newIndex < 0) {
                        playbackDirection = 1;
                        newIndex = 1; // Start going forward from second frame
                        if (newIndex >= frameCount) newIndex = frameCount - 1;
                        LOG.info("Reversing video playback direction (forward)");
                    }
                    currentFrameIndex.set(newIndex);
                } else {
                    // Normal mode: loop or stop at end
                    if (newIndex >= frameCount) {
                        if (loop.isOn()) {
                            currentFrameIndex.set(0);
                            LOG.info("Looping video back to frame 0");
                        } else {
                            currentFrameIndex.set(frameCount - 1);
                            playing.setValue(false);
                        }
                    } else if (newIndex < 0) {
                        // Shouldn't happen in normal mode, but handle it
                        currentFrameIndex.set(0);
                    } else {
                        currentFrameIndex.set(newIndex);
                    }
                }
            }
        } else {
            // Debug why we're not animating
            if (!hasLoggedEmpty && !hasLoggedLoading && currentFrames != null) {
                LOG.info("Not animating: playing={}, isLoading={}", playing.isOn(), isLoading.get());
            }
        }
        
        int frameIndex = currentFrameIndex.get();
        
        if (currentFrames == null || frameIndex >= frameCount) {
            return;
        }
        
        // Calculate interpolation for smooth slow-motion
        double interpolationFactor = frameAccumulator;
        int nextFrameIndex;
        if (playbackDirection > 0) {
            // Forward playback
            nextFrameIndex = (frameIndex + 1) % frameCount;
        } else {
            // Backward playback
            nextFrameIndex = frameIndex - 1;
            if (nextFrameIndex < 0) {
                nextFrameIndex = pingPong.isOn() ? 0 : frameCount - 1;
            }
        }
        
        int[][] currentFramePixels = currentFrames[frameIndex];
        int[][] nextFramePixels = currentFrames[nextFrameIndex];
        
        if (currentFramePixels == null) {
            return;
        }
        
        double xRange = bounds.maxX - bounds.minX;
        double zRange = bounds.maxZ - bounds.minZ;
        
        double effectiveScale = scale.getValue();
        double videoXScale, videoZScale;
        
        if (preserveAspect.isOn()) {
            // Preserve aspect ratio
            double fixtureAspect = xRange / zRange;
            // Video is rotated 90 CCW, so swap width/height for aspect ratio
            double videoAspect = (double) frameHeight / frameWidth;
            
            if (videoAspect > fixtureAspect) {
                videoXScale = effectiveScale;
                videoZScale = effectiveScale * fixtureAspect / videoAspect;
            } else {
                videoZScale = effectiveScale;
                videoXScale = effectiveScale * videoAspect / fixtureAspect;
            }
        } else {
            // Stretch to fill - both scales are the same
            videoXScale = effectiveScale;
            videoZScale = effectiveScale;
        }
        
        double bright = brightness.getValue();
        
        for (LXPoint p : model.points) {
            // Only render on pixels in the selected plane
            if (!bounds.isInPlane(p)) {
                continue;
            }
            
            // Map LED coordinates to normalized space
            double normalizedX = (p.x - bounds.minX) / xRange - 0.5;
            double normalizedZ = (p.z - bounds.minZ) / zRange - 0.5;
            
            // Apply offsets
            normalizedX -= xOffset.getValue();
            normalizedZ -= yOffset.getValue();
            
            // Apply scaling
            normalizedX /= videoXScale;
            normalizedZ /= videoZScale;
            
            // Map to video coordinates with 90 CCW rotation
            // LED X maps to video Y (vertical in rotated video)
            // LED Z maps to video X (horizontal in rotated video) 
            double videoX = normalizedZ + 0.5;
            double videoY = normalizedX + 0.5;
            
            if (videoX < 0 || videoX >= 1 || videoY < 0 || videoY >= 1) {
                continue;
            }
            
            int pixelX = (int) (videoX * (frameWidth - 1));
            int pixelY = (int) (videoY * (frameHeight - 1));
            
            try {
                // Get pixel from our int array [y][x]
                int rgb = currentFramePixels[pixelY][pixelX];
                
                // If interpolation is enabled and we're playing slowly, blend frames
                if (interpolate.isOn() && playbackSpeed.getValue() < 1.0 && nextFramePixels != null && interpolationFactor > 0) {
                    int nextRgb = nextFramePixels[pixelY][pixelX];
                    
                    // Extract ARGB components from both frames
                    int a1 = (rgb >> 24) & 0xFF;
                    int r1 = (rgb >> 16) & 0xFF;
                    int g1 = (rgb >> 8) & 0xFF;
                    int b1 = rgb & 0xFF;
                    
                    int a2 = (nextRgb >> 24) & 0xFF;
                    int r2 = (nextRgb >> 16) & 0xFF;
                    int g2 = (nextRgb >> 8) & 0xFF;
                    int b2 = nextRgb & 0xFF;
                    
                    // Linear interpolation between frames
                    int alpha = (int) (a1 + (a2 - a1) * interpolationFactor);
                    int r = (int) (r1 + (r2 - r1) * interpolationFactor);
                    int g = (int) (g1 + (g2 - g1) * interpolationFactor);
                    int b = (int) (b1 + (b2 - b1) * interpolationFactor);
                    
                    if (alpha == 0) {
                        continue;
                    }
                    
                    r = (int) Math.min(255, r * bright);
                    g = (int) Math.min(255, g * bright);
                    b = (int) Math.min(255, b * bright);
                    
                    colors[p.index] = LXColor.rgba(r, g, b, alpha);
                } else {
                    // No interpolation - use current frame as-is
                    int alpha = (rgb >> 24) & 0xFF;
                    if (alpha == 0) {
                        continue;
                    }
                    
                    int r = (int) Math.min(255, ((rgb >> 16) & 0xFF) * bright);
                    int g = (int) Math.min(255, ((rgb >> 8) & 0xFF) * bright);
                    int b = (int) Math.min(255, (rgb & 0xFF) * bright);
                    
                    colors[p.index] = LXColor.rgba(r, g, b, alpha);
                }
            } catch (Exception e) {
                LOG.error("Error getting pixel at ({}, {}): {}", pixelX, pixelY, e.getMessage());
            }
        }
    }
    
    @Override
    public void dispose() {
        if (currentLoadTask != null) {
            currentLoadTask.cancel(true);
        }
        if (loadingExecutor != null) {
            loadingExecutor.shutdown();
        }
        
        // Release buffer on dispose
        int[][][] currentBuffer = framePixels.getAndSet(null);
        if (currentBuffer != null) {
            bufferPool.releaseBuffer(currentBuffer);
        }
        numFrames.set(0);
        currentFrameIndex.set(0);
        
        super.dispose();
    }
}