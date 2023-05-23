package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import heronarts.lx.pattern.LXPattern;
import org.iqe.Audio;
import org.iqe.LOG;
import org.iqe.OscBridge;
import org.iqe.Sync;

/***
 * Cycle soloing through model children / fixtures, illuminating orientation, and dump tags
 */
@LXCategory(LXCategory.TEST)
public class DiagnosticsPattern extends LXPattern {
    private final Sync sync;
    public DiagnosticsPattern(LX lx) {
        super(lx);
        sync = new Sync(this);
    }

    @Override
    protected void run(double v) {
        // First black out everything
        for (LXPoint p : model.points) colors[p.index] = LXColor.BLACK;

        // Light up a fraction of current fixture (indicates orientation)
        LXModel child = model.children[(sync.step() / 4) % model.children.length];
        int i = 0;
        for (LXPoint p : child.points) {
            if (i++ / (double) child.points.length < sync.basis()) colors[p.index] = LXColor.WHITE;
        }

        // Diagnostic logging and event
        if (sync.step() % 4 == 0 && sync.isTriggering()) {
            String info = LOG.format("Fixture tags: {}, metadata: {}", child.tags, child.metaData);
            LOG.info(info);
            Audio.get().osc.event(OscBridge.Event.DIAGNOSTIC, info);
        }
    }
}
