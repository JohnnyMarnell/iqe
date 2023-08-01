package org.iqe;

import heronarts.lx.*;
import heronarts.lx.model.LXModel;
import heronarts.lx.studio.LXStudio;
import org.iqe.pattern.*;
import org.iqe.pattern.EqVisualizerPattern;
import org.iqe.pattern.pixelblaze.PixelblazePatterns;
import org.iqe.pattern.pixelblaze.UIPixelblazePattern;
import titanicsend.pattern.pixelblaze.PBAudio1;
import titanicsend.pattern.pixelblaze.PBFireworkNova;
import titanicsend.pattern.pixelblaze.PBXorcery;

import java.io.File;
import java.util.stream.Stream;

@LXPlugin.Name("IQE")
public class LXPluginIQE implements LXPlugin, LX.ProjectListener, LX.Listener, LXModel.Listener {
    public static final String INTERNAL = "NO_TOUCHY";
    protected LX lx;
    protected boolean running = false;

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

                PBXorcery.class,
                PBAudio1.class,
                PBFireworkNova.class,
                PixelblazePatterns.PixelBlazeBlowser.class,
                PixelblazePatterns.PBTemp.class,

                DiagnosticsPattern.class,
                BassBreathPattern.class
        ).forEach(lx.registry::addPattern);

        running = true;
    }

    public void initializeUI(LXStudio lx, LXStudio.UI ui) {
      ((LXStudio.Registry)lx.registry).addUIDeviceControls(UIPixelblazePattern.class);
    }

    public void onUIReady(LXStudio lx, LXStudio.UI ui) {

    }

    @Override
    public void projectChanged(File file, Change change) {
        if (change == LX.ProjectListener.Change.OPEN) {
            LOG.info("Project open, dumping OSC state for clients");
            Audio.get().osc.refresh();
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
