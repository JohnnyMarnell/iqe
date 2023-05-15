package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import heronarts.lx.pattern.LXPattern;

public class BouncingDotsPattern extends LXPattern {
    private final Sync sync;
    public BouncingDotsPattern(LX lx) {
        super(lx);
        sync = new Sync(this);
    }

    @Override
    protected void run(double v) {
        if (sync.stale()) return;
        double phase = Math.sin(2 * Math.PI * sync.basis()) / 2;

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
