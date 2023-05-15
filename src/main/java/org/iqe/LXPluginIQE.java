package org.iqe;

import heronarts.lx.*;
import org.iqe.pattern.*;

import java.util.stream.Stream;

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

        Stream.of(
                ZipStripPattern.class,
                HolyTrinitiesPattern.class,
                PillarFirePattern.class,
                BouncingDotsPattern.class,
                BassBreathPattern.class
        ).forEach(lx.registry::addPattern);

        lx.addProjectListener((file, change) -> {
            if (change == LX.ProjectListener.Change.OPEN) {
                LOG.info("Project open, dumping OSC state for clients");
                Audio.get().osc.command("/lx/osc-query");
            }
        });
    }
}
