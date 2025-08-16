package org.iqe;

import heronarts.lx.*;
import heronarts.lx.mixer.LXAbstractChannel;
import heronarts.lx.mixer.LXChannel;
import heronarts.lx.model.LXModel;
import heronarts.lx.pattern.LXPattern;
import heronarts.lx.pattern.LifePattern;
import heronarts.lx.pattern.color.GradientPattern;
import heronarts.lx.pattern.color.SolidPattern;
import heronarts.lx.pattern.form.ChevronPattern;
import heronarts.lx.pattern.form.OrboxPattern;
import heronarts.lx.pattern.form.PlanesPattern;
import heronarts.lx.pattern.strip.ChasePattern;
import heronarts.lx.pattern.texture.NoisePattern;
import heronarts.lx.pattern.texture.SparklePattern;
import heronarts.lx.studio.LXStudio;
import jkbstudio.autopilot.AutopilotLibrary;
import jkbstudio.autopilot.AutopilotLibrary.AutoParameter;
import jkbstudio.autopilot.AutopilotLibrary.Scale;
import jkbstudio.autopilot.UIAutopilot;

import org.iqe.pattern.*;
import org.iqe.pattern.EqVisualizerPattern;
import org.iqe.pattern.pixelblaze.PixelBlazeBlowser;
import org.iqe.pattern.pixelblaze.PixelblazePatterns;
import org.iqe.pattern.pixelblaze.UIPixelblazePattern;
import titanicsend.pattern.pixelblaze.PBAudio1;
import titanicsend.pattern.pixelblaze.PBFireworkNova;
import titanicsend.pattern.pixelblaze.PBXorcery;

import java.io.File;
import java.util.stream.Stream;

@LXPlugin.Name("IQE")
public class LXPluginIQE implements LXStudio.Plugin, LX.ProjectListener, LX.Listener, LXModel.Listener {
    public static final String INTERNAL = "NO_TOUCHY";
    protected LX lx;
    protected boolean running = false;

    AutopilotIQE autopilot;

    public LXPluginIQE(LX lx) {
      this.lx = lx;
    }

    @Override
    public void dispose() {
        if (!running) return;
        running = false;
        LOG.info("IQE Shutting down");
        Audio.get().dispose();
    }

    @Override
    public void initialize(LX lx) {
        lx.getModel().addListener(this);
        lx.addListener(this);
        lx.addProjectListener(this);
        Audio.initialize(lx);
        AudioModulators.initialize(lx);

        Stream.of(
                ZipStripPattern.class,
                HolyTrinitiesPattern.class,
                PillarFirePattern.class,
                BouncingDotsPattern.class,
                PianoRollPattern.class,
                MindLikeWaterPattern.class,
                EqVisualizerPattern.class,
                PongPattern.class,
                ImagePattern.class,
                VideoPattern.class,

                PBXorcery.class,
                PBAudio1.class,
                PBFireworkNova.class,
                PixelBlazeBlowser.class,
                PixelblazePatterns.PBTemp.class,

                DiagnosticColorCyclePattern.class,
                DiagnosticsPattern.class,
                BassBreathPattern.class
        ).forEach(lx.registry::addPattern);

        lx.registry.addFixture(FlamecasterFixtures.NECorner.class);
        lx.registry.addFixture(FlamecasterFixtures.NWCorner.class);
        lx.registry.addFixture(DMXParCanFixture.class);
        lx.registry.addFixture(SmoothDMXParCanFixture.class);

        initializeAutopilot();

        running = true;
    }

    public static class ChannelListener implements LXChannel.Listener {
        @Override
        public void patternWillChange(LXChannel channel, LXPattern pattern, LXPattern nextPattern) {
            // TODO(jmarnell) - sigh, this never fires?
            LOG.info("Channel {} changing from {} to {}", channel.getLabel(), pattern.getLabel(), nextPattern.getLabel());
        }
    }
    ChannelListener channelListener = new ChannelListener();

    static public final double SLOWMIN = 30;
    static public final double SLOWMAX = 90;

    public void initializeAutopilot() {
        this.autopilot = new AutopilotIQE(lx);
        lx.engine.registerComponent("autopilot", this.autopilot);

        // Tell autopilot which parameters to animate
        AutopilotLibrary library = this.autopilot.library;

        /* 
         * Patterns used on COLOR channels
         */

        // Gradient
        library.addPattern(GradientPattern.class)
            .addParameter(new AutoParameter("gradient", Scale.ABSOLUTE, .75, 1))
            .addParameter(new AutoParameter("xAmount", Scale.ABSOLUTE, .7, 1, SLOWMIN, SLOWMAX))
            .addParameter(new AutoParameter("rotate", Scale.ABSOLUTE, 1, 1, 0))   // force rotate on
            .addParameter(new AutoParameter("yaw", Scale.ABSOLUTE, 0, 360, 120))
            ;

        /*
         *  Patterns used on both COLOR and PATTERN channels
         */

        // Noise is both a color and pattern
        library.addPattern(NoisePattern.class)
            .addParameter(new AutoParameter("scale", Scale.ABSOLUTE, 22, 80, 0))  // Randomize 22-80
            .addParameter(new AutoParameter("midpoint", Scale.ABSOLUTE, 20, 80, 40))
            .addParameter(new AutoParameter("xScale", Scale.NORMALIZED, .25, .75, .1))
            .addParameter(new AutoParameter("yScale", Scale.NORMALIZED, 0, 1, .2))
            .addParameter(new AutoParameter("contrast", Scale.ABSOLUTE, 100, 400, 100))
            .addParameter(new AutoParameter("motionSpeed", Scale.ABSOLUTE, .6, .9, .1))
            .addParameter(new AutoParameter("xMotion", Scale.NORMALIZED, 0, 1, .5))
            .addParameter(new AutoParameter("yMotion", Scale.NORMALIZED, 0, 1, .5))
            ;

        /*
         *  Patterns used on PATTERN channels
         */

        // Chase
        library.addPattern(ChasePattern.class)
            .addParameter(new AutoParameter("speed", Scale.ABSOLUTE, -20, 40, 20))
            .addParameter(new AutoParameter("size", Scale.ABSOLUTE, 20, 70, 40))
            .addParameter(new AutoParameter("fade", Scale.ABSOLUTE, 20, 60, 20))
            .addParameter(new AutoParameter("chunkSize", Scale.ABSOLUTE, 20, 80, 0))
            .addParameter(new AutoParameter("shift", Scale.ABSOLUTE, 0, 70, 14))
            ;

        // Chevron
        library.addPattern(ChevronPattern.class)
            .addParameter(new AutoParameter("speed", Scale.ABSOLUTE, 45, 75, 20))
            .addParameter(new AutoParameter("xAmt", Scale.ABSOLUTE, 0, 1, .2))
            .addParameter(new AutoParameter("zAmt", Scale.ABSOLUTE, 0, 1, SLOWMIN, SLOWMAX, .5))
            .addParameter(new AutoParameter("sharp", Scale.ABSOLUTE, 1.7, 30, SLOWMIN, SLOWMAX, 20))
            .addParameter(new AutoParameter("stripes", Scale.ABSOLUTE, 1, 4, SLOWMIN, SLOWMAX, 1.75))
            .addParameter(new AutoParameter("yaw", Scale.ABSOLUTE, 0, 360, SLOWMIN, SLOWMAX, 120))
            .addParameter(new AutoParameter("pitch", Scale.ABSOLUTE, 0, 180, SLOWMIN, SLOWMAX))
            ;

        // Life (deprecated)
        library.addPattern(LifePattern.class)
          .addParameter(new AutoParameter("translateX", Scale.ABSOLUTE, -.7, .7, .9))
          .addParameter(new AutoParameter("yaw", Scale.ABSOLUTE, 0, 360, 180))
          .addParameter(new AutoParameter("translateY", Scale.ABSOLUTE, -.4, .7, SLOWMIN, SLOWMAX, .2))
          .addParameter(new AutoParameter("expand", Scale.ABSOLUTE, 1, 3, 1))
          .addParameter(new AutoParameter("pitch", Scale.ABSOLUTE, 175, 211, SLOWMIN, SLOWMAX, 20))
          ;


        // Orbox
        library.addPattern(OrboxPattern.class)
            .addParameter(new AutoParameter("shapeLerp", Scale.NORMALIZED, 0, 1, .5))
            .addParameter(new AutoParameter("fill", Scale.NORMALIZED, 0, .5, .3))
            .addParameter(new AutoParameter("radius", Scale.ABSOLUTE, 0, 100, 50))
            .addParameter(new AutoParameter("width", Scale.ABSOLUTE, 0, 8, 4 ))
            .addParameter(new AutoParameter("fade", Scale.ABSOLUTE, 5, 100, 30))
            .addParameter(new AutoParameter("xAmt", Scale.ABSOLUTE, 40, 90, 25))
            .addParameter(new AutoParameter("zAmt", Scale.ABSOLUTE, 40, 90, 25))
            .addParameter(new AutoParameter("yaw", Scale.ABSOLUTE, 0, 360, SLOWMIN, SLOWMAX, 180))
            .addParameter(new AutoParameter("shearY", Scale.NORMALIZED, 0, 1, SLOWMIN, SLOWMAX, .7))
            ;

        // Planes
        library.addPattern(PlanesPattern.class)
            .addParameter(new AutoParameter("layer/1/position", Scale.NORMALIZED, 0, 1, .4))  // Check to see if layered patterns work
            ;

        // Solid
        library.addPattern(SolidPattern.class)
            .addParameter(new AutoParameter("hue", Scale.NORMALIZED, 0, 1, .2))
            .addParameter(new AutoParameter("saturation", Scale.NORMALIZED, 0, 1, .3))
            ;

        // Sparkle
        library.addPattern(SparklePattern.class)
            .addParameter(new AutoParameter("maxLevel", Scale.ABSOLUTE, 50, 100, 30))
            .addParameter(new AutoParameter("minLevel", Scale.ABSOLUTE, 42, 70, 20))
            .addParameter(new AutoParameter("density", Scale.ABSOLUTE, 10, 180, SLOWMIN, SLOWMAX, 50))
            .addParameter(new AutoParameter("sharp", Scale.ABSOLUTE, -.5, .5, .3))
            ;        

        // BassBreath
        library.addPattern(BassBreathPattern.class)
            .addParameter(new AutoParameter("Brightness", Scale.NORMALIZED, 0, 1, .4))
            .addParameter(new AutoParameter("MinBand", Scale.NORMALIZED, 0, 1, .3))
            .addParameter(new AutoParameter("NumBands", Scale.NORMALIZED, 0, 1, .1))
            ;

        // ZipStrip
        library.addPattern(ZipStripPattern.class)
            .addParameter(new AutoParameter("energy", Scale.NORMALIZED, 0, 1, .5))
            ;
        
        // PB:
        // PBAudio1
        // PBFireworkNova
        // PBTemp
        // PBXorcery   
        // PixelBlazeBlowser
        
        // Add parameters to these:
        // MindLikeWater
        // HolyTrinities
        // PillarFire
        // PianoRoll
        // EqVisualizer
        // BouncingDots
    }

    public void projectOpen() {
        LOG.info("Project open, dumping OSC state for clients");
        Audio.get().osc.refresh();

        LOG.info("LX number of mixer channels {}", lx.engine.mixer.getChannels().size());
        lx.engine.mixer.getChannels().forEach(c -> LOG.info("Adding listener that never fires for channel name: {}", c.label.getString()));
        lx.engine.mixer.getChannels().forEach(c -> c.addListener(channelListener));
        
        // Reset solo channel to 0 after project loads to avoid accidental soloing
        if (this.autopilot != null) {
            this.autopilot.soloChannel.setValue(0);
            LOG.info("Reset solo channel to 0 after project load");
        }
        
        // Set up OSC string listener for testing
        setupOscStringListener();
    }
    
    private void setupOscStringListener() {
        // Listen for string messages on /iqe/string path
        Audio.get().osc.on("/iqe/string", msg -> {
            try {
                // Try to get string from the message
                String receivedString = msg.getString(0);
                LOG.info("OSC String received: '{}'", receivedString);
                
                // You could also broadcast it back out or trigger other actions
                Audio.get().osc.sendOutgoing("/iqe/string/echo", receivedString);
            } catch (Exception e) {
                LOG.error("Error processing OSC string message: {}", e.getMessage());
            }
        });
        
        // Listen for command messages on /iqe/cmd
        Audio.get().osc.on("/iqe/cmd", msg -> {
            try {
                if (msg.size() >= 1) {
                    String fullCommand = msg.getString(0);
                    LOG.info("OSC Command received: '{}'", fullCommand);
                    
                    // Split by whitespace, with limit of 2 to keep everything after first space together
                    String[] parts = fullCommand.split("\\s+", 2);
                    
                    if (parts.length >= 2) {
                        String command = parts[0].toLowerCase();
                        String arg = parts[1];
                        
                        LOG.info("Parsed command: '{}' with arg: '{}'", command, arg);
                        
                        if ("solo".equals(command)) {
                            handleSoloCommand(arg);
                        } else {
                            LOG.info("Unknown command: '{}'", command);
                        }
                    } else {
                        LOG.error("OSC Command must be in format: 'command argument'");
                    }
                } else {
                    LOG.error("OSC Command requires at least 1 string argument");
                }
            } catch (Exception e) {
                LOG.error("Error processing OSC command: {}", e.getMessage());
            }
        });
        
        // Also listen for test messages with multiple arguments
        Audio.get().osc.on("/iqe/test", msg -> {
            LOG.info("OSC Test message received with {} arguments", msg.size());
            String typeTag = msg.getTypeTag().toString();
            for (int i = 0; i < msg.size(); i++) {
                try {
                    char type = typeTag.charAt(i);
                    // Try different types
                    if (type == 's') {
                        LOG.info("  Arg[{}] (string): '{}'", i, msg.getString(i));
                    } else if (type == 'f') {
                        LOG.info("  Arg[{}] (float): {}", i, msg.getFloat(i));
                    } else if (type == 'i') {
                        LOG.info("  Arg[{}] (int): {}", i, msg.getInt(i));
                    } else {
                        LOG.info("  Arg[{}] (type '{}'): [raw data]", i, type);
                    }
                } catch (Exception e) {
                    LOG.info("  Arg[{}]: unable to parse ({})", i, e.getMessage());
                }
            }
        });
        
        LOG.info("OSC String listeners registered on /iqe/string, /iqe/cmd and /iqe/test");
    }
    
    private void handleSoloCommand(String channelNamePattern) {
        // Find channel by name (case-insensitive partial match)
        String pattern = channelNamePattern.toLowerCase();
        
        // Search through all channels to find a match
        int channelIndex = 0;
        boolean found = false;
        
        for (LXAbstractChannel channel : lx.engine.mixer.getChannels()) {
            if (channel.getLabel().toLowerCase().contains(pattern)) {
                LOG.info("Found matching channel: '{}' at index {}", channel.getLabel(), channelIndex);
                
                // Use autopilot's solo functionality
                if (this.autopilot != null) {
                    // Set the solo channel value (1-based index for the UI parameter)
                    this.autopilot.soloChannel.setValue(channelIndex + 1);
                    LOG.info("Solo activated for channel '{}'", channel.getLabel());
                } else {
                    LOG.error("Autopilot not initialized");
                }
                
                found = true;
                break;
            }
            channelIndex++;
        }
        
        if (!found) {
            LOG.info("No channel found matching pattern: '{}'", channelNamePattern);
            // Could also send feedback via OSC
            Audio.get().osc.sendOutgoing("/iqe/cmd/response", "error", "No channel found: " + channelNamePattern);
        } else {
            // Send success feedback
            Audio.get().osc.sendOutgoing("/iqe/cmd/response", "success", "Solo activated: " + channelNamePattern);
        }
    }

    @Override
    public void initializeUI(LXStudio lx, LXStudio.UI ui) {
        LXStudio.Registry registry = (LXStudio.Registry) lx.registry;
        registry.addUIDeviceControls(UIPixelblazePattern.class);
    }

    @Override
    public void onUIReady(LXStudio lx, LXStudio.UI ui) {
        new UIAutopilot(ui, this.autopilot, ui.leftPane.global.getContentWidth())
                .addToContainer(ui.leftPane.global, 0);
    }

    @Override
    public void projectChanged(File file, Change change) {
        if (change == LX.ProjectListener.Change.OPEN) {
            projectOpen();
        }
    }

    @Override
    public void modelChanged(LX lx, LXModel model) {
        LOG.info("LX Model changed: {}, {} children, {} points", System.identityHashCode(model),
                model.children.length, model.points.length);
        model.addListener(this);
        LX.Listener.super.modelChanged(lx, model);
    }

    @Override
    public void modelGenerationChanged(LX lx, LXModel model) {
        LOG.info("LX Model generaishe changed: {}, {} children, {} points", System.identityHashCode(model),
                model.children.length, model.points.length);
        LX.Listener.super.modelGenerationChanged(lx, model);
    }

    @Override
    public void modelGenerationUpdated(LXModel model) {
        LOG.info("LXModel generaishe updaitz: {}, {} children, {} points", System.identityHashCode(model),
                model.children.length, model.points.length);
    }
}
