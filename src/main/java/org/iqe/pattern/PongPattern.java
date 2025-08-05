package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import heronarts.lx.parameter.BooleanParameter;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.pattern.LXPattern;
import org.iqe.LOG;

import java.util.Random;

@LXCategory(LXCategory.TEST)
public class PongPattern extends LXPattern {
    
    // Game parameters
    private final CompoundParameter ballSpeed = new CompoundParameter("ballSpeed", 0.5, 0.1, 2.0)
        .setDescription("Speed of the ball");
    
    private final CompoundParameter paddleSpeed = new CompoundParameter("paddleSpeed", 1.0, 0.1, 3.0)
        .setDescription("Speed of AI paddle movement");
    
    private final CompoundParameter paddleSize = new CompoundParameter("paddleSize", 0.2, 0.1, 0.5)
        .setDescription("Size of paddles as fraction of width");
    
    private final CompoundParameter randomness = new CompoundParameter("randomness", 0.3, 0, 1.0)
        .setDescription("Amount of randomness in ball bounces");
    
    private final CompoundParameter ballSize = new CompoundParameter("ballSize", 0.05, 0.02, 0.15)
        .setDescription("Size of the ball");
    
    private final BooleanParameter autoPlay = new BooleanParameter("autoPlay", true)
        .setDescription("AI controls both paddles");
    
    private final CompoundParameter aiSkill = new CompoundParameter("aiSkill", 0.8, 0.1, 1.0)
        .setDescription("AI difficulty level");
    
    // Game state
    private double ballX = 0.5;
    private double ballZ = 0.5;
    private double ballVX = 0.3;
    private double ballVZ = 0.3;
    
    private double topPaddleX = 0.5;
    private double bottomPaddleX = 0.5;
    
    private int topScore = 0;
    private int bottomScore = 0;
    
    private final Random random = new Random();
    
    // Cached bounds
    private double minX = Double.MAX_VALUE;
    private double maxX = Double.MIN_VALUE;
    private double minZ = Double.MAX_VALUE;
    private double maxZ = Double.MIN_VALUE;
    private boolean boundsCalculated = false;
    
    public PongPattern(LX lx) {
        super(lx);
        addParameter(ballSpeed);
        addParameter(paddleSpeed);
        addParameter(paddleSize);
        addParameter(randomness);
        addParameter(ballSize);
        addParameter(autoPlay);
        addParameter(aiSkill);
        
        // Initialize ball with random direction
        double angle = random.nextDouble() * Math.PI * 2;
        ballVX = Math.cos(angle) * 0.3;
        ballVZ = Math.sin(angle) * 0.3;
    }
    
    private void calculateBounds() {
        for (LXModel child : model.children) {
            for (LXPoint p : child.points) {
                minX = Math.min(minX, p.x);
                maxX = Math.max(maxX, p.x);
                minZ = Math.min(minZ, p.z);
                maxZ = Math.max(maxZ, p.z);
            }
        }
        boundsCalculated = true;
        LOG.info("PongPattern bounds: X[{}, {}], Z[{}, {}]", minX, maxX, minZ, maxZ);
    }
    
    @Override
    protected void run(double deltaMs) {
        if (!boundsCalculated) {
            calculateBounds();
        }
        
        // Clear all pixels
        for (LXPoint p : model.points) {
            colors[p.index] = LXColor.CLEAR;
        }
        
        double deltaSeconds = deltaMs / 1000.0;
        double speed = ballSpeed.getValue();
        
        // Update ball position
        ballX += ballVX * speed * deltaSeconds;
        ballZ += ballVZ * speed * deltaSeconds;
        
        // Ball collision with left/right walls
        if (ballX < 0) {
            ballX = 0;
            ballVX = Math.abs(ballVX);
            addRandomness();
        } else if (ballX > 1) {
            ballX = 1;
            ballVX = -Math.abs(ballVX);
            addRandomness();
        }
        
        // Paddle collision detection
        double paddleWidth = paddleSize.getValue();
        double paddleHeight = 0.08; // Height in Z-space
        
        // Top paddle collision (near Z=0)
        if (ballZ < paddleHeight && ballVZ < 0) {
            if (Math.abs(ballX - topPaddleX) < paddleWidth / 2 + ballSize.getValue() / 2) {
                ballZ = paddleHeight;
                ballVZ = Math.abs(ballVZ);
                // Add spin based on where ball hits paddle
                double hitOffset = (ballX - topPaddleX) / (paddleWidth / 2);
                ballVX += hitOffset * 0.7; // Even more spin for dynamic gameplay
                
                // Add a small speed boost on paddle hits
                ballVZ *= 1.1;
                addRandomness();
            }
        }
        
        // Bottom paddle collision (near Z=1)
        if (ballZ > 1 - paddleHeight && ballVZ > 0) {
            if (Math.abs(ballX - bottomPaddleX) < paddleWidth / 2 + ballSize.getValue() / 2) {
                ballZ = 1 - paddleHeight;
                ballVZ = -Math.abs(ballVZ);
                // Add spin based on where ball hits paddle
                double hitOffset = (ballX - bottomPaddleX) / (paddleWidth / 2);
                ballVX += hitOffset * 0.7; // Even more spin for dynamic gameplay
                
                // Add a small speed boost on paddle hits
                ballVZ *= 1.1;
                addRandomness();
            }
        }
        
        // Score when ball goes out of bounds
        if (ballZ < 0) {
            bottomScore++;
            resetBall();
            LOG.info("Bottom player scores! Score: Top {} - Bottom {}", topScore, bottomScore);
        } else if (ballZ > 1) {
            topScore++;
            resetBall();
            LOG.info("Top player scores! Score: Top {} - Bottom {}", topScore, bottomScore);
        }
        
        // AI paddle movement
        if (autoPlay.getValueb()) {
            movePaddleAI(true, deltaSeconds);
            movePaddleAI(false, deltaSeconds);
        } else {
            movePaddleAI(true, deltaSeconds);
            // Bottom paddle could be controlled by user input if we had it
        }
        
        // Normalize ball velocity and maintain minimum speed
        double velocity = Math.sqrt(ballVX * ballVX + ballVZ * ballVZ);
        double minVelocity = 0.3; // Minimum speed
        double maxVelocity = 0.8; // Maximum speed
        
        if (velocity < minVelocity) {
            // Speed up if too slow
            ballVX = (ballVX / velocity) * minVelocity;
            ballVZ = (ballVZ / velocity) * minVelocity;
            velocity = minVelocity;
        } else if (velocity > maxVelocity) {
            // Slow down if too fast
            ballVX = (ballVX / velocity) * maxVelocity;
            ballVZ = (ballVZ / velocity) * maxVelocity;
            velocity = maxVelocity;
        }
        
        // Prevent ball from getting too vertical - more aggressive correction
        double minHorizontalRatio = 0.4; // Minimum 40% horizontal movement (increased from 30%)
        double horizontalRatio = Math.abs(ballVX) / velocity;
        
        if (horizontalRatio < minHorizontalRatio) {
            // Force more horizontal movement
            double targetHorizontalVel = velocity * minHorizontalRatio;
            double targetVerticalVel = velocity * Math.sqrt(1 - minHorizontalRatio * minHorizontalRatio);
            
            // Add horizontal velocity in a random direction if needed
            if (Math.abs(ballVX) < 0.1) {
                ballVX = (random.nextBoolean() ? 1 : -1) * targetHorizontalVel;
            } else {
                ballVX = Math.signum(ballVX) * targetHorizontalVel;
            }
            
            // Maintain total velocity while reducing vertical component
            ballVZ = Math.signum(ballVZ) * targetVerticalVel;
        }
        
        // Draw the game
        drawGame();
    }
    
    private void movePaddleAI(boolean isTop, double deltaSeconds) {
        double targetX = ballX;
        double currentX = isTop ? topPaddleX : bottomPaddleX;
        double skill = aiSkill.getValue();
        
        // Add some imperfection to AI
        if (random.nextDouble() > skill) {
            targetX += (random.nextDouble() - 0.5) * 0.2;
        }
        
        // Only move if ball is coming towards paddle
        boolean ballComingTowards = isTop ? (ballVZ < 0) : (ballVZ > 0);
        if (!ballComingTowards && skill < 0.9) {
            return; // Don't move if ball is going away (unless AI is very skilled)
        }
        
        // Move paddle towards target
        double diff = targetX - currentX;
        double moveSpeed = paddleSpeed.getValue() * deltaSeconds;
        
        if (Math.abs(diff) > moveSpeed) {
            diff = Math.signum(diff) * moveSpeed;
        }
        
        double newX = currentX + diff;
        newX = Math.max(paddleSize.getValue() / 2, Math.min(1 - paddleSize.getValue() / 2, newX));
        
        if (isTop) {
            topPaddleX = newX;
        } else {
            bottomPaddleX = newX;
        }
    }
    
    private void addRandomness() {
        double rand = randomness.getValue();
        ballVX += (random.nextDouble() - 0.5) * rand * 0.5; // More X randomness
        ballVZ += (random.nextDouble() - 0.5) * rand * 0.3; // Bit more Z randomness too
        
        // Small chance of a "power bounce" for excitement
        if (random.nextDouble() < 0.1) {
            ballVX *= 1.2;
            ballVZ *= 1.2;
        }
    }
    
    private void resetBall() {
        ballX = 0.5;
        ballZ = 0.5;
        
        // Random starting direction with better angle distribution
        // Avoid angles too close to vertical (90 or 270 degrees)
        double angle;
        do {
            angle = random.nextDouble() * Math.PI * 2;
        } while (Math.abs(Math.cos(angle)) < 0.3); // Ensure at least 30% horizontal component
        
        ballVX = Math.cos(angle) * 0.4;
        ballVZ = Math.sin(angle) * 0.4;
    }
    
    private void drawGame() {
        double xRange = maxX - minX;
        double zRange = maxZ - minZ;
        
        for (LXPoint p : model.points) {
            // Normalize point position
            double normalizedX = (p.x - minX) / xRange;
            double normalizedZ = (p.z - minZ) / zRange;
            
            // Draw ball
            double ballDist = Math.sqrt(Math.pow(normalizedX - ballX, 2) + Math.pow(normalizedZ - ballZ, 2));
            if (ballDist < ballSize.getValue()) {
                double intensity = 1 - (ballDist / ballSize.getValue());
                colors[p.index] = LXColor.hsb(0, 0, intensity * 100);
                continue;
            }
            
            // Draw paddles
            double paddleWidth = paddleSize.getValue();
            double paddleHeight = 0.06;
            
            // Top paddle
            if (normalizedZ < paddleHeight && Math.abs(normalizedX - topPaddleX) < paddleWidth / 2) {
                colors[p.index] = LXColor.hsb(200, 100, 80); // Blue paddle
                continue;
            }
            
            // Bottom paddle
            if (normalizedZ > 1 - paddleHeight && Math.abs(normalizedX - bottomPaddleX) < paddleWidth / 2) {
                colors[p.index] = LXColor.hsb(0, 100, 80); // Red paddle
                continue;
            }
            
            // Draw center line
            if (Math.abs(normalizedZ - 0.5) < 0.01 && (int)(normalizedX * 20) % 2 == 0) {
                colors[p.index] = LXColor.hsb(0, 0, 30); // Dim white dashed line
            }
        }
    }
}