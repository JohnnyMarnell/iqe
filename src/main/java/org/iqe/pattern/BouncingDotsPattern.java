package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import heronarts.lx.modulator.SinLFO;
import heronarts.lx.pattern.LXPattern;
import org.iqe.Sync;

public class BouncingDotsPattern extends LXPattern {
    protected final Sync sync;
    protected final SinLFO phase;

    public BouncingDotsPattern(LX lx) {
        super(lx);
        sync = new Sync(this);
        phase = new SinLFO(0, 1, sync.periodMs);
        startModulator(phase);
    }

    @Override
    protected void run(double v) {
        if (sync.stale()) return;
        double phase = this.phase.getValue();

        int dotColor = LXColor.WHITE;
        int dotWidth = 10;
        for (LXModel edge : model.children) {
            int target = (int) (edge.size * phase);
            int i = 0;
            for (LXPoint point : edge.points) {
                int noHigherThan = target + dotWidth / 2;
                int tooLow = noHigherThan - dotWidth;
                if (i <= tooLow || i > noHigherThan) {
                    colors[point.index] = LXColor.CLEAR;
                } else {
                    colors[point.index] = dotColor;
                }
                i++;
            }
        }
    }
}
