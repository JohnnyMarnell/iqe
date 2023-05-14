package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.color.LXColor;
import heronarts.lx.pattern.LXPattern;

import static org.iqe.Geometry.colorize;
import static org.iqe.Geometry.points;

public class PillarFirePattern extends LXPattern {
    public final Sync sync;
    public PillarFirePattern(LX lx) {
        super(lx);
        this.sync = new Sync(this);
    }

    @Override
    protected void run(double v) {
        colorize(this, point -> LXColor.WHITE);
        if (sync.stale()) return;
        colorize(this, point -> point.yn == 1.0 ? LXColor.WHITE : LXColor.BLACK);
        points(this)
                .filter(point -> point.yn < sync.basis())
                .forEach(point -> colors[point.index] = LXColor.rgba(255, 255, 255, (int)
                        /* point.yn * 255 */
                        /* TEMath.easeOutPow(point.yn, .78) * 255) */
                        Math.pow(2, 4 * (point.yn - 1))
                        ));

    }
}
