package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.color.LXColor;
import heronarts.lx.pattern.LXPattern;

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
        colorize(this, point -> LXColor.WHITE);
        if (sync.stale()) return;

        // todo: trying different ease / ramp functions for "fire" motion upward
        // double fireHeight = sync.basis();
        // double fireHeight = TEMath.easeOutPow(sync.basis(), .78);
        double fireHeight = Math.pow(2, 4 * (sync.basis() - 1));

        int fireColor = LXColor.rgba(255, 255, 255, (int) fireHeight * 255);

        // Ceiling stays as is / do nothing (white), darken pillar above fire, and light fire
        colorize(this, point ->
                point.yn == 1. ? LXColor.WHITE :
                point.yn > fireHeight ? LXColor.BLACK :
                fireColor
        );
    }
}
