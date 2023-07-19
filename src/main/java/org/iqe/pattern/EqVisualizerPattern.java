package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.audio.GraphicMeter;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.pattern.LXPattern;
import org.iqe.Audio;

public class EqVisualizerPattern extends LXPattern {
    public EqVisualizerPattern(LX lx) {
        super(lx);
    }

    @Override
    protected void run(double v) {
        GraphicMeter graphicMeter = Audio.get().graphicMeter();

        for (LXPoint p : this.model.points) {
            int bandIndex = (p.xn == 1.0) ? graphicMeter.numBands - 1 : (int) (p.xn * graphicMeter.numBands);

            double val = graphicMeter.getBand(bandIndex);
            double minZ = 0.5 - val * 0.5;
            double maxZ = 0.5 + val * 0.5;

            this.colors[p.index] = p.zn >= minZ && p.zn <= maxZ ? LXColor.WHITE : LXColor.CLEAR;
        }
    }
}
