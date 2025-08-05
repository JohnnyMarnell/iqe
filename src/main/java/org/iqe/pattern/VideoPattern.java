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
import org.bytedeco.javacv.*;

@LXCategory(LXCategory.TEST)
public class VideoPattern extends LXPattern {
    
    private static final int MAX_RESAMPLED_WIDTH = 420;
    private static final int MAX_RESAMPLED_HEIGHT = 240;
    private static final int MAX_FRAMES_IN_MEMORY = 150;
    private static final int FRAME_LOAD_BATCH_SIZE = 10;
    
    final StringParameter videoPath = new StringParameter("videoPath", "src/main/resources/videos/sample.webm")
        .setDescription("Path to the video file");
    
    private final CompoundParameter playbackSpeed = new CompoundParameter("speed", 1.0, 0.1, 4.0)
        .setDescription("Playback speed multiplier");
    
    private final BooleanParameter loop = new BooleanParameter("loop", true)
        .setDescription("Loop the video");
    
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
    
    private final ExecutorService loadingExecutor = Executors.newSingleThreadExecutor(r -> {
        Thread t = new Thread(r, "VideoPattern-Loader");
        t.setDaemon(true);
        return t;
    });
    
    volatile List<BufferedImage> frames = new ArrayList<>();
    volatile boolean isLoading = false;
    private volatile String loadingStatus = "";
    private volatile String currentVideoPath = "";
    private volatile int currentFrameIndex = 0;
    private volatile double frameAccumulator = 0;
    private volatile double fps = 30.0;
    private volatile int resampledWidth = MAX_RESAMPLED_WIDTH;
    private volatile int resampledHeight = MAX_RESAMPLED_HEIGHT;
    
    private Future<?> currentLoadTask = null;
    private boolean hasLoggedEmpty = false;
    private boolean hasLoggedLoading = false;
    
    private double minX = Double.MAX_VALUE;
    private double maxX = Double.MIN_VALUE;
    private double minZ = Double.MAX_VALUE;
    private double maxZ = Double.MIN_VALUE;
    private double targetY = Double.MIN_VALUE;
    private boolean boundsCalculated = false;
    
    public VideoPattern(LX lx) {
        super(lx);
        LOG.info("VideoPattern constructor starting");
        addParameter(videoPath);
        addParameter(playbackSpeed);
        addParameter(loop);
        addParameter(playing);
        addParameter(scale);
        addParameter(xOffset);
        addParameter(yOffset);
        addParameter(brightness);
        
        // Don't load in constructor - let run() trigger it
        LOG.info("VideoPattern constructor completed, video will load on first run");
    }
    
    @Override
    protected void onActive() {
        super.onActive();
        // Ensure colors array is initialized when pattern becomes active
        if (this.colors == null && this.model != null) {
            this.colors = new int[this.model.points.length];
        }
    }
    
    private void calculateBounds() {
        for (LXModel child : model.children) {
            for (LXPoint p : child.points) {
                if (p.y > targetY) {
                    targetY = p.y;
                }
            }
        }
        
        double threshold = targetY - 10;
        for (LXModel child : model.children) {
            for (LXPoint p : child.points) {
                if (p.y >= threshold) {
                    minX = Math.min(minX, p.x);
                    maxX = Math.max(maxX, p.x);
                    minZ = Math.min(minZ, p.z);
                    maxZ = Math.max(maxZ, p.z);
                }
            }
        }
        
        boundsCalculated = true;
        LOG.info("VideoPattern bounds calculated: X[{}, {}], Z[{}, {}], targetY: {}", 
                 minX, maxX, minZ, maxZ, targetY);
    }
    
    private void loadVideoAsync(String path) {
        LOG.info("loadVideoAsync called for path: {}", path);
        if (isLoading) {
            LOG.info("Video is already loading, skipping new load request");
            return;
        }
        
        if (currentLoadTask != null && !currentLoadTask.isDone()) {
            LOG.info("Cancelling previous load task");
            currentLoadTask.cancel(true);
        }
        
        isLoading = true;
        loadingStatus = "Loading...";
        LOG.info("Starting background load task for: {}", path);
        
        currentLoadTask = loadingExecutor.submit(() -> {
            LOG.info("Background thread started for loading: {}", path);
            long startTime = System.currentTimeMillis();
            try {
                loadVideoInBackground(path);
                long duration = System.currentTimeMillis() - startTime;
                LOG.info("Video loading completed in {} ms", duration);
            } catch (Exception e) {
                LOG.error("Failed to load video in background: {}", e.getMessage(), e);
                loadingStatus = "Error: " + e.getMessage();
            } finally {
                isLoading = false;
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
            loadingStatus = "File not found";
            return;
        }
        
        LOG.info("Video file exists: {} (size: {} bytes)", file.getAbsolutePath(), file.length());
        
        FFmpegFrameGrabber grabber = null;
        Java2DFrameConverter converter = new Java2DFrameConverter();
        List<BufferedImage> newFrames = new ArrayList<>();
        
        try {
            loadingStatus = "Opening video...";
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
            
            int framesToLoad = Math.min(totalFrames, MAX_FRAMES_IN_MEMORY);
            int frameSkip = totalFrames > MAX_FRAMES_IN_MEMORY ? totalFrames / MAX_FRAMES_IN_MEMORY : 1;
            
            LOG.info("Planning to load {} frames (skip every {} frames) from total of {} frames", 
                     framesToLoad, frameSkip, totalFrames);
            
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
                        newFrames.add(resampledImage);
                        loadedFrames++;
                        
                        long frameProcessTime = System.currentTimeMillis() - frameProcessStart;
                        if (loadedFrames % FRAME_LOAD_BATCH_SIZE == 0) {
                            loadingStatus = String.format("Loading... %d/%d frames", loadedFrames, framesToLoad);
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
            
            LOG.info("Updating frame buffer with {} new frames", newFrames.size());
            frames = newFrames;
            fps = videoFps;
            resampledWidth = targetWidth;
            resampledHeight = targetHeight;
            currentFrameIndex = 0;
            frameAccumulator = 0;
            
            loadingStatus = "";
            LOG.info("Successfully loaded {} frames from video (resampled to {}x{})", 
                     newFrames.size(), targetWidth, targetHeight);
            
        } catch (FrameGrabber.Exception e) {
            LOG.error("Error loading video: {}", e.getMessage(), e);
            loadingStatus = "Error: " + e.getMessage();
            frames = new ArrayList<>();
        } catch (Exception e) {
            LOG.error("Unexpected error loading video: {}", e.getMessage(), e);
            loadingStatus = "Error: " + e.getMessage();
            frames = new ArrayList<>();
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
        // Ensure colors array is initialized
        if (this.colors == null) {
            if (this.model != null) {
                this.colors = new int[this.model.points.length];
            } else {
                return; // Can't proceed without model
            }
        }
        
        if (!videoPath.getString().equals(currentVideoPath)) {
            LOG.info("Video path changed from '{}' to '{}'", currentVideoPath, videoPath.getString());
            currentVideoPath = videoPath.getString();
            loadVideoAsync(currentVideoPath);
        }
        
        if (!boundsCalculated) {
            calculateBounds();
        }
        
        for (LXPoint p : model.points) {
            colors[p.index] = LXColor.CLEAR;
        }
        
        List<BufferedImage> currentFrames = frames;
        if (currentFrames.isEmpty()) {
            if (isLoading) {
                if (!hasLoggedLoading) {
                    LOG.info("Frames empty, loading in progress: {}", loadingStatus);
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
        
        if (playing.isOn() && !isLoading) {
            double frameDelta = (deltaMs / 1000.0) * fps * playbackSpeed.getValue();
            frameAccumulator += frameDelta;
            
            while (frameAccumulator >= 1.0) {
                frameAccumulator -= 1.0;
                currentFrameIndex++;
                
                if (currentFrameIndex >= currentFrames.size()) {
                    if (loop.isOn()) {
                        currentFrameIndex = 0;
                    } else {
                        currentFrameIndex = currentFrames.size() - 1;
                        playing.setValue(false);
                    }
                }
            }
        }
        
        int frameIndex = currentFrameIndex;
        
        if (frameIndex >= currentFrames.size()) {
            return;
        }
        
        BufferedImage currentFrame = currentFrames.get(frameIndex);
        if (currentFrame == null) {
            return;
        }
        
        double xRange = maxX - minX;
        double zRange = maxZ - minZ;
        
        double fixtureAspect = xRange / zRange;
        double videoAspect = (double) frameWidth / frameHeight;
        
        double effectiveScale = scale.getValue();
        double videoXScale, videoZScale;
        
        if (videoAspect > fixtureAspect) {
            videoXScale = effectiveScale;
            videoZScale = effectiveScale * fixtureAspect / videoAspect;
        } else {
            videoZScale = effectiveScale;
            videoXScale = effectiveScale * videoAspect / fixtureAspect;
        }
        
        double threshold = targetY - 10;
        double bright = brightness.getValue();
        
        for (LXPoint p : model.points) {
            if (p.y < threshold) {
                continue;
            }
            
            double normalizedX = (p.x - minX) / xRange - 0.5;
            double normalizedZ = (p.z - minZ) / zRange - 0.5;
            
            normalizedX -= xOffset.getValue();
            normalizedZ -= yOffset.getValue();
            
            normalizedX /= videoXScale;
            normalizedZ /= videoZScale;
            
            double videoX = normalizedX + 0.5;
            double videoY = normalizedZ + 0.5;
            
            if (videoX < 0 || videoX >= 1 || videoY < 0 || videoY >= 1) {
                continue;
            }
            
            int pixelX = (int) (videoX * (frameWidth - 1));
            int pixelY = (int) (videoY * (frameHeight - 1));
            
            try {
                int rgb = currentFrame.getRGB(pixelX, pixelY);
                
                int alpha = (rgb >> 24) & 0xFF;
                if (alpha == 0) {
                    continue;
                }
                
                int r = (int) Math.min(255, ((rgb >> 16) & 0xFF) * bright);
                int g = (int) Math.min(255, ((rgb >> 8) & 0xFF) * bright);
                int b = (int) Math.min(255, (rgb & 0xFF) * bright);
                
                colors[p.index] = LXColor.rgba(r, g, b, alpha);
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
        loadingExecutor.shutdown();
        
        frames = new ArrayList<>();
        
        super.dispose();
    }
}