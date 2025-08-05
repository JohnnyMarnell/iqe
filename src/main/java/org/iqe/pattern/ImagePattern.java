package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.DiscreteParameter;
import heronarts.lx.parameter.StringParameter;
import heronarts.lx.pattern.LXPattern;
import org.iqe.LOG;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.File;
import java.io.IOException;

@LXCategory(LXCategory.TEST)
public class ImagePattern extends LXPattern {
    
    private BufferedImage image;
    private String currentImagePath = "";
    
    private final StringParameter imagePath = new StringParameter("imagePath", "src/main/resources/images/heart-8075.png")
        .setDescription("Path to the PNG image file");
    
    private final CompoundParameter scale = new CompoundParameter("scale", 1.0, 0.1, 5.0)
        .setDescription("Scale factor for the image");
    
    private final CompoundParameter xOffset = new CompoundParameter("xOffset", 0, -1, 1)
        .setDescription("Horizontal offset");
    
    private final CompoundParameter yOffset = new CompoundParameter("yOffset", 0, -1, 1)
        .setDescription("Vertical offset");
    
    private final DiscreteParameter colorMode = new DiscreteParameter("colorMode", new String[]{"RGB", "Grayscale", "Red", "Green", "Blue"}, 0)
        .setDescription("Color extraction mode");
    
    private final CompoundParameter rotation = new CompoundParameter("rotation", 90, 0, 360)
        .setDescription("Rotation angle in degrees");
    
    private final CompoundParameter bounceSpeed = new CompoundParameter("bounceSpeed", 0, 0, 5)
        .setDescription("Bounce speed (0 = static)");
    
    // Cached bounds for the highest fixtures
    private double minX = Double.MAX_VALUE;
    private double maxX = Double.MIN_VALUE;
    private double minZ = Double.MAX_VALUE;
    private double maxZ = Double.MIN_VALUE;
    private double targetY = Double.MIN_VALUE;
    private boolean boundsCalculated = false;
    
    // Bounce animation state
    private double bounceX = 0;
    private double bounceZ = 0;
    private double velocityX = 1;
    private double velocityZ = 0.7; // Different ratio for more interesting motion
    
    public ImagePattern(LX lx) {
        super(lx);
        addParameter(imagePath);
        addParameter(scale);
        addParameter(xOffset);
        addParameter(yOffset);
        addParameter(colorMode);
        addParameter(rotation);
        addParameter(bounceSpeed);
        
        loadImage(imagePath.getString());
    }
    
    private void calculateBounds() {
        // Find the highest Y value (ceiling fixtures)
        for (LXModel child : model.children) {
            for (LXPoint p : child.points) {
                if (p.y > targetY) {
                    targetY = p.y;
                }
            }
        }
        
        // Now find the bounds of only the highest fixtures
        double threshold = targetY - 10; // Allow some tolerance
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
        LOG.info("ImagePattern bounds calculated: X[{}, {}], Z[{}, {}], targetY: {}", 
                 minX, maxX, minZ, maxZ, targetY);
    }
    
    private void loadImage(String path) {
        try {
            File file = new File(path);
            if (file.exists()) {
                image = ImageIO.read(file);
                LOG.info("Loaded image: {} ({}x{})", path, image.getWidth(), image.getHeight());
            } else {
                LOG.error("Image file not found: {}", path);
                image = null;
            }
        } catch (IOException e) {
            LOG.error("Error loading image: {}", e.getMessage());
            image = null;
        }
    }
    
    @Override
    protected void run(double deltaMs) {
        // Check if we need to reload the image
        if (!imagePath.getString().equals(currentImagePath)) {
            currentImagePath = imagePath.getString();
            loadImage(currentImagePath);
        }
        
        // Calculate bounds if needed
        if (!boundsCalculated) {
            calculateBounds();
        }
        
        // Clear all pixels first
        for (LXPoint p : model.points) {
            colors[p.index] = LXColor.CLEAR;
        }
        
        // If no image loaded, just return
        if (image == null) {
            return;
        }
        
        double xRange = maxX - minX;
        double zRange = maxZ - minZ;
        
        // Calculate aspect ratios
        double fixtureAspect = xRange / zRange;
        double imageAspect = (double) image.getWidth() / image.getHeight();
        
        // Calculate scale to fit image proportionally
        double effectiveScale = scale.getValue();
        double imageXScale, imageZScale;
        
        if (imageAspect > fixtureAspect) {
            // Image is wider - fit to width
            imageXScale = effectiveScale;
            imageZScale = effectiveScale * fixtureAspect / imageAspect;
        } else {
            // Image is taller - fit to height
            imageZScale = effectiveScale;
            imageXScale = effectiveScale * imageAspect / fixtureAspect;
        }
        
        // Update bounce position if speed is non-zero
        double speed = bounceSpeed.getValue();
        if (speed > 0) {
            // Calculate movement in normalized space
            double deltaSeconds = deltaMs / 1000.0;
            double movement = speed * deltaSeconds * 0.3; // Scale down for reasonable speed
            
            bounceX += velocityX * movement;
            bounceZ += velocityZ * movement;
            
            // Calculate bounds for collision detection
            // The image can move until its edge hits the fixture bounds
            double maxBounceX = 0.5 - (imageXScale / 2);
            double maxBounceZ = 0.5 - (imageZScale / 2);
            
            // Check collisions and reverse direction
            if (bounceX > maxBounceX) {
                bounceX = maxBounceX;
                velocityX = -Math.abs(velocityX);
            } else if (bounceX < -maxBounceX) {
                bounceX = -maxBounceX;
                velocityX = Math.abs(velocityX);
            }
            
            if (bounceZ > maxBounceZ) {
                bounceZ = maxBounceZ;
                velocityZ = -Math.abs(velocityZ);
            } else if (bounceZ < -maxBounceZ) {
                bounceZ = -maxBounceZ;
                velocityZ = Math.abs(velocityZ);
            }
        }
        
        // Calculate rotation in radians
        double rotationRad = Math.toRadians(rotation.getValue());
        double cosRot = Math.cos(rotationRad);
        double sinRot = Math.sin(rotationRad);
        
        // Apply to pixels
        double threshold = targetY - 10; // Same threshold as bounds calculation
        
        for (LXPoint p : model.points) {
            // Only render on the highest fixtures
            if (p.y < threshold) {
                continue;
            }
            
            // Normalize position within the bounds
            double normalizedX = (p.x - minX) / xRange - 0.5; // -0.5 to 0.5
            double normalizedZ = (p.z - minZ) / zRange - 0.5; // -0.5 to 0.5
            
            // Apply offset (including bounce offset)
            normalizedX -= xOffset.getValue() + bounceX;
            normalizedZ -= yOffset.getValue() + bounceZ;
            
            // Apply rotation around center
            double rotatedX = normalizedX * cosRot - normalizedZ * sinRot;
            double rotatedZ = normalizedX * sinRot + normalizedZ * cosRot;
            
            // Apply scale
            rotatedX /= imageXScale;
            rotatedZ /= imageZScale;
            
            // Convert to image coordinates (0 to 1)
            double imageX = rotatedX + 0.5;
            double imageY = rotatedZ + 0.5;
            
            // Check bounds
            if (imageX < 0 || imageX >= 1 || imageY < 0 || imageY >= 1) {
                continue;
            }
            
            // Sample the image
            int pixelX = (int) (imageX * (image.getWidth() - 1));
            int pixelY = (int) (imageY * (image.getHeight() - 1));
            
            int rgb = image.getRGB(pixelX, pixelY);
            
            // Extract alpha channel
            int alpha = (rgb >> 24) & 0xFF;
            
            // Skip fully transparent pixels
            if (alpha == 0) {
                continue;
            }
            
            // Extract color based on mode
            int color;
            switch (colorMode.getValuei()) {
                case 0: // RGB
                    // Preserve alpha channel in RGB mode
                    color = rgb;
                    break;
                case 1: // Grayscale
                    int gray = (int) (0.299 * ((rgb >> 16) & 0xFF) + 
                                      0.587 * ((rgb >> 8) & 0xFF) + 
                                      0.114 * (rgb & 0xFF));
                    color = LXColor.rgba(gray, gray, gray, alpha);
                    break;
                case 2: // Red only
                    color = LXColor.rgba((rgb >> 16) & 0xFF, 0, 0, alpha);
                    break;
                case 3: // Green only
                    color = LXColor.rgba(0, (rgb >> 8) & 0xFF, 0, alpha);
                    break;
                case 4: // Blue only
                    color = LXColor.rgba(0, 0, rgb & 0xFF, alpha);
                    break;
                default:
                    color = rgb;
            }
            
            colors[p.index] = color;
        }
    }
}