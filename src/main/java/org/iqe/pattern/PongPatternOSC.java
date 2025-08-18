package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.color.LXColor;
import heronarts.lx.mixer.LXChannel;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import heronarts.lx.osc.LXOscComponent;
import heronarts.lx.osc.OscMessage;
import heronarts.lx.parameter.BooleanParameter;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.pattern.LXPattern;
import org.iqe.LOG;

import java.util.Random;
import java.util.Timer;
import java.util.TimerTask;

@LXCategory(LXCategory.TEST)
public class PongPatternOSC extends LXPattern implements LXOscComponent {
    
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
    
    private final BooleanParameter autoPlay = new BooleanParameter("autoPlay", false)
        .setDescription("AI controls both paddles");
    
    private final CompoundParameter aiSkill = new CompoundParameter("aiSkill", 0.8, 0.1, 1.0)
        .setDescription("AI difficulty level");
    
    // OSC Control parameters - normalized 0-1 for paddle positions
    private final CompoundParameter paddle1Control = new CompoundParameter("paddle1", 0.5, 0, 1)
        .setDescription("Player 1 paddle position (top)");
    
    private final CompoundParameter paddle2Control = new CompoundParameter("paddle2", 0.5, 0, 1)
        .setDescription("Player 2 paddle position (bottom)");
    
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
    
    // Auto-disable tracking
    private long lastManualControlTime = 0;
    private static final long AUTO_DISABLE_TIMEOUT_MS = 30000; // 30 seconds
    private Timer autoDisableTimer = null;
    private LXChannel myChannel = null;
    private boolean wasManuallyControlled = false;
    
    public PongPatternOSC(LX lx) {
        super(lx);
        addParameter(ballSpeed);
        addParameter(paddleSpeed);
        addParameter(paddleSize);
        addParameter(randomness);
        addParameter(ballSize);
        addParameter(autoPlay);
        addParameter(aiSkill);
        addParameter(paddle1Control);
        addParameter(paddle2Control);
        
        // Initialize ball with random direction
        double angle = random.nextDouble() * Math.PI * 2;
        ballVX = Math.cos(angle) * 0.3;
        ballVZ = Math.sin(angle) * 0.3;
        
        // Listen for paddle control changes
        paddle1Control.addListener(p -> {
            LOG.info("Pong: Paddle 1 moved to {}", paddle1Control.getValue());
            onPaddleControlled(1);
        });
        paddle2Control.addListener(p -> {
            LOG.info("Pong: Paddle 2 moved to {}", paddle2Control.getValue());
            onPaddleControlled(2);
        });
    }
    
    private void onPaddleControlled(int player) {
        lastManualControlTime = System.currentTimeMillis();
        
        // Enable channel and disable auto-play whenever paddle is controlled
        if (!wasManuallyControlled) {
            wasManuallyControlled = true;
            LOG.info("Pong: Manual control activated! Player {} is playing", player);
        }
        
        // Always disable autoplay and enable channel when controlled
        autoPlay.setValue(false);
        enableMyChannel();
        
        // Reset or start the auto-disable timer
        resetAutoDisableTimer();
    }
    
    private void enableMyChannel() {
        // Find our channel and enable it
        if (myChannel == null) {
            for (heronarts.lx.mixer.LXAbstractChannel abstractChannel : lx.engine.mixer.getChannels()) {
                if (abstractChannel instanceof LXChannel) {
                    LXChannel channel = (LXChannel) abstractChannel;
                    for (LXPattern pattern : channel.getPatterns()) {
                        if (pattern == this) {
                            myChannel = channel;
                            break;
                        }
                    }
                    if (myChannel != null) break;
                }
            }
        }
        
        if (myChannel != null && !myChannel.enabled.getValueb()) {
            myChannel.enabled.setValue(true);
            LOG.info("Pong: Channel enabled for gameplay!");
        }
    }
    
    private void resetAutoDisableTimer() {
        // Cancel existing timer
        if (autoDisableTimer != null) {
            autoDisableTimer.cancel();
        }
        
        // Start new timer
        autoDisableTimer = new Timer();
        autoDisableTimer.schedule(new TimerTask() {
            @Override
            public void run() {
                onInactivityTimeout();
            }
        }, AUTO_DISABLE_TIMEOUT_MS);
    }
    
    private void onInactivityTimeout() {
        LOG.info("Pong: No activity for 30 seconds, disabling channel and returning to auto-play");
        
        // Re-enable auto-play
        autoPlay.setValue(true);
        wasManuallyControlled = false;
        
        // Reset paddles to center
        paddle1Control.setValue(0.5);
        paddle2Control.setValue(0.5);
        
        // Disable the channel
        if (myChannel != null) {
            myChannel.enabled.setValue(false);
        }
        
        // Cancel the timer so it doesn't keep running
        if (autoDisableTimer != null) {
            autoDisableTimer.cancel();
            autoDisableTimer = null;
        }
        
        // Reset scores
        topScore = 0;
        bottomScore = 0;
        resetBall();
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
            
            // Ensure ball doesn't bounce too vertically off walls
            double minAngle = 0.4; // Minimum ratio of horizontal to total velocity
            double totalVel = Math.sqrt(ballVX * ballVX + ballVZ * ballVZ);
            if (Math.abs(ballVX) < totalVel * minAngle) {
                ballVX = totalVel * minAngle;
                ballVZ = Math.signum(ballVZ) * Math.sqrt(totalVel * totalVel - ballVX * ballVX);
            }
            
            addRandomness();
        } else if (ballX > 1) {
            ballX = 1;
            ballVX = -Math.abs(ballVX);
            
            // Ensure ball doesn't bounce too vertically off walls
            double minAngle = 0.4; // Minimum ratio of horizontal to total velocity
            double totalVel = Math.sqrt(ballVX * ballVX + ballVZ * ballVZ);
            if (Math.abs(ballVX) < totalVel * minAngle) {
                ballVX = -totalVel * minAngle;
                ballVZ = Math.signum(ballVZ) * Math.sqrt(totalVel * totalVel - ballVX * ballVX);
            }
            
            addRandomness();
        }
        
        // Update paddle positions based on control mode
        if (autoPlay.getValueb()) {
            // Both paddles AI controlled
            movePaddleAI(true, deltaSeconds);
            movePaddleAI(false, deltaSeconds);
        } else {
            // Manual control from OSC - direct mapping: 1 = right/max, 0 = left/min
            topPaddleX = paddle1Control.getValue();
            bottomPaddleX = paddle2Control.getValue();
        }
        
        // Paddle collision detection
        double paddleWidth = paddleSize.getValue();
        double paddleHeight = 0.08; // Height in Z-space
        
        // Top paddle collision (near Z=0)
        if (ballZ < paddleHeight && ballVZ < 0) {
            if (Math.abs(ballX - topPaddleX) < paddleWidth / 2 + ballSize.getValue() / 2) {
                ballZ = paddleHeight;
                ballVZ = Math.abs(ballVZ);
                // Add MORE spin based on where ball hits paddle - increased from 0.7 to 1.2
                double hitOffset = (ballX - topPaddleX) / (paddleWidth / 2);
                ballVX += hitOffset * 1.2;
                
                // If hit near edge of paddle, add extra horizontal velocity
                if (Math.abs(hitOffset) > 0.7) {
                    ballVX *= 1.3;
                    ballVZ *= 0.8; // Reduce vertical speed on edge hits
                } else {
                    ballVZ *= 1.1;
                }
                
                // Ensure minimum horizontal movement after paddle hit
                if (Math.abs(ballVX) < 0.2) {
                    ballVX = (hitOffset > 0 ? 1 : -1) * 0.3;
                }
                
                addRandomness();
            }
        }
        
        // Bottom paddle collision (near Z=1)
        if (ballZ > 1 - paddleHeight && ballVZ > 0) {
            if (Math.abs(ballX - bottomPaddleX) < paddleWidth / 2 + ballSize.getValue() / 2) {
                ballZ = 1 - paddleHeight;
                ballVZ = -Math.abs(ballVZ);
                // Add MORE spin based on where ball hits paddle - increased from 0.7 to 1.2
                double hitOffset = (ballX - bottomPaddleX) / (paddleWidth / 2);
                ballVX += hitOffset * 1.2;
                
                // If hit near edge of paddle, add extra horizontal velocity
                if (Math.abs(hitOffset) > 0.7) {
                    ballVX *= 1.3;
                    ballVZ *= 0.8; // Reduce vertical speed on edge hits
                } else {
                    ballVZ *= 1.1;
                }
                
                // Ensure minimum horizontal movement after paddle hit
                if (Math.abs(ballVX) < 0.2) {
                    ballVX = (hitOffset > 0 ? 1 : -1) * 0.3;
                }
                
                addRandomness();
            }
        }
        
        // Score when ball goes out of bounds
        if (ballZ < 0) {
            bottomScore++;
            resetBall();
            LOG.info("Player 2 scores! Score: P1 {} - P2 {}", topScore, bottomScore);
        } else if (ballZ > 1) {
            topScore++;
            resetBall();
            LOG.info("Player 1 scores! Score: P1 {} - P2 {}", topScore, bottomScore);
        }
        
        // Normalize ball velocity
        normalizeVelocity();
        
        // Draw the game
        drawGame();
    }
    
    private void normalizeVelocity() {
        double velocity = Math.sqrt(ballVX * ballVX + ballVZ * ballVZ);
        double minVelocity = 0.3;
        double maxVelocity = 0.8;
        
        if (velocity < minVelocity) {
            ballVX = (ballVX / velocity) * minVelocity;
            ballVZ = (ballVZ / velocity) * minVelocity;
            velocity = minVelocity;
        } else if (velocity > maxVelocity) {
            ballVX = (ballVX / velocity) * maxVelocity;
            ballVZ = (ballVZ / velocity) * maxVelocity;
            velocity = maxVelocity;
        }
        
        // MUCH more aggressive prevention of vertical movement
        double minHorizontalRatio = 0.5; // Increased from 0.4 - at least 50% horizontal
        double horizontalRatio = Math.abs(ballVX) / velocity;
        
        if (horizontalRatio < minHorizontalRatio) {
            double targetHorizontalVel = velocity * minHorizontalRatio;
            double targetVerticalVel = velocity * Math.sqrt(1 - minHorizontalRatio * minHorizontalRatio);
            
            // Always ensure significant horizontal movement
            if (Math.abs(ballVX) < 0.2) { // Increased threshold
                // Add random horizontal velocity if too low
                ballVX = (random.nextBoolean() ? 1 : -1) * targetHorizontalVel * (1 + random.nextDouble() * 0.3);
            } else {
                ballVX = Math.signum(ballVX) * targetHorizontalVel;
            }
            
            ballVZ = Math.signum(ballVZ) * targetVerticalVel;
        }
        
        // Extra check: if ball is moving too vertically, add random horizontal kick
        if (Math.abs(ballVZ) > Math.abs(ballVX) * 1.5) {
            ballVX += (random.nextDouble() - 0.5) * 0.3;
        }
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
            return;
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
        // More aggressive randomness to prevent patterns
        ballVX += (random.nextDouble() - 0.5) * rand * 0.7;  // Increased from 0.5
        ballVZ += (random.nextDouble() - 0.5) * rand * 0.4;  // Increased from 0.3
        
        // Higher chance of speed variations
        if (random.nextDouble() < 0.2) {  // Increased from 0.1
            ballVX *= 1.1 + random.nextDouble() * 0.2;  // More variation
            ballVZ *= 1.1 + random.nextDouble() * 0.2;
        }
        
        // Always add a small random kick to horizontal movement
        ballVX += (random.nextDouble() - 0.5) * 0.1;
    }
    
    private void resetBall() {
        ballX = 0.5;
        ballZ = 0.5;
        
        double angle;
        do {
            angle = random.nextDouble() * Math.PI * 2;
        } while (Math.abs(Math.cos(angle)) < 0.3);
        
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
            
            // Draw ball - make it rainbow colored when manually controlled!
            double ballDist = Math.sqrt(Math.pow(normalizedX - ballX, 2) + Math.pow(normalizedZ - ballZ, 2));
            if (ballDist < ballSize.getValue()) {
                double intensity = 1 - (ballDist / ballSize.getValue());
                if (wasManuallyControlled) {
                    // Rainbow ball during manual play
                    colors[p.index] = LXColor.hsb(
                        (float)((System.currentTimeMillis() / 10) % 360),
                        100,
                        intensity * 100
                    );
                } else {
                    colors[p.index] = LXColor.hsb(0, 0, intensity * 100);
                }
                continue;
            }
            
            // Draw paddles
            double paddleWidth = paddleSize.getValue();
            double paddleHeight = 0.06;
            
            // Top paddle (Player 1)
            if (normalizedZ < paddleHeight && Math.abs(normalizedX - topPaddleX) < paddleWidth / 2) {
                colors[p.index] = LXColor.hsb(200, 100, wasManuallyControlled ? 100 : 80); // Brighter when controlled
                continue;
            }
            
            // Bottom paddle (Player 2)
            if (normalizedZ > 1 - paddleHeight && Math.abs(normalizedX - bottomPaddleX) < paddleWidth / 2) {
                colors[p.index] = LXColor.hsb(0, 100, wasManuallyControlled ? 100 : 80); // Brighter when controlled
                continue;
            }
            
            // Draw center line
            if (Math.abs(normalizedZ - 0.5) < 0.01 && (int)(normalizedX * 20) % 2 == 0) {
                colors[p.index] = LXColor.hsb(0, 0, 30);
            }
        }
    }
    
    // LXOscComponent implementation
    @Override
    public String getOscAddress() {
        return "/lx/pattern/pong";
    }
    
    @Override
    public boolean handleOscMessage(OscMessage message, String[] parts, int index) {
        if (parts.length > index) {
            String param = parts[index];
            
            // Handle paddle control messages
            if ("paddle1".equals(param) || "pong1".equals(param)) {
                if (message.size() > 0) {
                    float value = message.getFloat(0);
                    paddle1Control.setValue(value);
                    return true;
                }
            } else if ("paddle2".equals(param) || "pong2".equals(param)) {
                if (message.size() > 0) {
                    float value = message.getFloat(0);
                    paddle2Control.setValue(value);
                    return true;
                }
            }
        }
        
        return super.handleOscMessage(message, parts, index);
    }
}