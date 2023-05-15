package org.iqe;

import heronarts.lx.*;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.modulation.LXModulationEngine;
import heronarts.lx.modulator.LXModulator;
import heronarts.lx.modulator.LXWaveshape;
import heronarts.lx.modulator.VariableLFO;
import heronarts.lx.osc.*;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.pattern.LXPattern;

import java.io.IOException;
import java.net.SocketException;
import java.net.UnknownHostException;
import java.util.*;
import java.util.function.Function;

public class LXPluginIQE implements LXPlugin {
    protected LX lx;

    @Override
    public void dispose() {
        LXPlugin.super.dispose();
    }

    @Override
    public void initialize(LX lx) {
        this.lx = lx;
        Audio.initialize(lx);
        AudioModulators.initialize(lx);

        lx.registry.addPattern(ZipStripPattern.class);
        lx.registry.addPattern(HolyTrinitiesPattern.class);
        lx.registry.addPattern(PillarFirePattern.class);
        lx.registry.addPattern(BouncingDotsPattern.class);
        lx.registry.addPattern(BassBreathPattern.class);

        lx.addProjectListener((file, change) -> {
            if (change == LX.ProjectListener.Change.OPEN) {
                LOG.info("Project open, dumping OSC state for clients");
                Audio.get().osc.command("/lx/osc-query");
            }
        });
    }
}
