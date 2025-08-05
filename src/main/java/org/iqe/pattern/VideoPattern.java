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
import org.bytedeco.javacv.*;

@LXCategory(LXCategory.TEST)
public class VideoPattern extends LXPattern {
    
    private final StringParameter videoPath = new StringParameter("videoPath", "src/main/resources/videos/sample.webm")
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
    
    private FFmpegFrameGrabber grabber;
    private Java2DFrameConverter converter;
    private List<BufferedImage> frames;
    private String currentVideoPath = "";
    private int currentFrameIndex = 0;
    private double frameAccumulator = 0;
    private double fps = 30.0;
    
    private double minX = Double.MAX_VALUE;
    private double maxX = Double.MIN_VALUE;
    private double minZ = Double.MAX_VALUE;
    private double maxZ = Double.MIN_VALUE;
    private double targetY = Double.MIN_VALUE;
    private boolean boundsCalculated = false;
    
    public VideoPattern(LX lx) {
        super(lx);
        addParameter(videoPath);
        addParameter(playbackSpeed);
        addParameter(loop);
        addParameter(playing);
        addParameter(scale);
        addParameter(xOffset);
        addParameter(yOffset);
        addParameter(brightness);
        
        converter = new Java2DFrameConverter();
        frames = new ArrayList<>();
        
        loadVideo(videoPath.getString());
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
    
    private void loadVideo(String path) {
        try {
            File file = new File(path);
            if (!file.exists()) {
                LOG.error("Video file not found: {}", path);
                return;
            }
            
            frames.clear();
            currentFrameIndex = 0;
            frameAccumulator = 0;
            
            if (grabber != null) {
                try {
                    grabber.stop();
                    grabber.release();
                } catch (Exception e) {
                    LOG.error("Error closing previous grabber: {}", e.getMessage());
                }
            }
            
            grabber = new FFmpegFrameGrabber(file);
            grabber.start();
            
            fps = grabber.getFrameRate();
            if (fps <= 0) fps = 30.0;
            
            LOG.info("Loading video: {} ({}x{}, {} fps, {} frames)", 
                     path, grabber.getImageWidth(), grabber.getImageHeight(), 
                     fps, grabber.getLengthInFrames());
            
            org.bytedeco.javacv.Frame frame;
            int frameCount = 0;
            int maxFrames = 300;
            
            while ((frame = grabber.grab()) != null && frameCount < maxFrames) {
                if (frame.image != null) {
                    BufferedImage bufferedImage = converter.convert(frame);
                    if (bufferedImage != null) {
                        frames.add(cloneImage(bufferedImage));
                        frameCount++;
                        
                        if (frameCount % 30 == 0) {
                            LOG.info("Loaded {} frames...", frameCount);
                        }
                    }
                }
            }
            
            grabber.stop();
            grabber.release();
            
            LOG.info("Successfully loaded {} frames from video", frames.size());
            
        } catch (FrameGrabber.Exception e) {
            LOG.error("Error loading video: {}", e.getMessage());
            frames.clear();
        }
    }
    
    private BufferedImage cloneImage(BufferedImage source) {
        BufferedImage clone = new BufferedImage(source.getWidth(), source.getHeight(), BufferedImage.TYPE_INT_ARGB);
        Graphics2D g = clone.createGraphics();
        g.drawImage(source, 0, 0, null);
        g.dispose();
        return clone;
    }
    
    @Override
    protected void run(double deltaMs) {
        if (!videoPath.getString().equals(currentVideoPath)) {
            currentVideoPath = videoPath.getString();
            loadVideo(currentVideoPath);
        }
        
        if (!boundsCalculated) {
            calculateBounds();
        }
        
        for (LXPoint p : model.points) {
            colors[p.index] = LXColor.CLEAR;
        }
        
        if (frames.isEmpty()) {
            return;
        }
        
        if (playing.isOn()) {
            double frameDelta = (deltaMs / 1000.0) * fps * playbackSpeed.getValue();
            frameAccumulator += frameDelta;
            
            while (frameAccumulator >= 1.0) {
                frameAccumulator -= 1.0;
                currentFrameIndex++;
                
                if (currentFrameIndex >= frames.size()) {
                    if (loop.isOn()) {
                        currentFrameIndex = 0;
                    } else {
                        currentFrameIndex = frames.size() - 1;
                        playing.setValue(false);
                    }
                }
            }
        }
        
        BufferedImage currentFrame = frames.get(currentFrameIndex);
        if (currentFrame == null) {
            return;
        }
        
        double xRange = maxX - minX;
        double zRange = maxZ - minZ;
        
        double fixtureAspect = xRange / zRange;
        double videoAspect = (double) currentFrame.getWidth() / currentFrame.getHeight();
        
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
            
            int pixelX = (int) (videoX * (currentFrame.getWidth() - 1));
            int pixelY = (int) (videoY * (currentFrame.getHeight() - 1));
            
            int rgb = currentFrame.getRGB(pixelX, pixelY);
            
            int alpha = (rgb >> 24) & 0xFF;
            if (alpha == 0) {
                continue;
            }
            
            int r = (int) Math.min(255, ((rgb >> 16) & 0xFF) * bright);
            int g = (int) Math.min(255, ((rgb >> 8) & 0xFF) * bright);
            int b = (int) Math.min(255, (rgb & 0xFF) * bright);
            
            colors[p.index] = LXColor.rgba(r, g, b, alpha);
        }
    }
    
    @Override
    public void dispose() {
        if (grabber != null) {
            try {
                grabber.stop();
                grabber.release();
            } catch (Exception e) {
                LOG.error("Error disposing grabber: {}", e.getMessage());
            }
        }
        frames.clear();
        super.dispose();
    }
}