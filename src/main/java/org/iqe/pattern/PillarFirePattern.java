package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.pattern.LXPattern;
import org.iqe.Sync;

import static heronarts.lx.color.LXColor.*;
import static org.iqe.Geometry.colorize;

public class PillarFirePattern extends LXPattern {
    public final Sync sync;
    public PillarFirePattern(LX lx) {
        super(lx);
        this.sync = new Sync(this, 1, false, false);
    }

    // todo: figure out color blending to simplify this and all patterns
    @Override
    protected void run(double v) {
        if (sync.stale()) return;

        // todo: trying different ease / ramp functions for "fire" motion upward
//         double fireHeight = sync.basis();
        // double fireHeight = TEMath.easeOutPow(sync.basis(), .78);
        double fireHeight = Math.pow(2, 4 * (sync.basis() - 1));

        // Ceiling stays as is / do nothing, darken pillar above fire, and light fire
        int fireColor = LXColor.rgba(255, 165, 255, 255);
        for (LXPoint point : model.points) {
            if (point.yn < fireHeight) colors[point.index] = LXColor.rgba(255, 165, 255, (int) (point.yn * 255));
            else if (point.yn < 1.) colors[point.index] = LXColor.BLACK;
        }
    }
}
