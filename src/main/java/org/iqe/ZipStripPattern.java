package org.iqe;


import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.pattern.LXPattern;

/**
 * From TE TempoReactiveEdge
 * https://github.com/titanicsend/LXStudio-TE
 */
@LXCategory(LXCategory.TEST)
public class ZipStripPattern extends LXPattern {
    public final CompoundParameter energy =
            new CompoundParameter("Energy", .22, .22, 1)
                    .setDescription("Pulse width and movement suddenness between tempo");
    public final Sync sync;

    public ZipStripPattern(LX lx) {
        super(lx);
        addParameter("energy", energy);
        sync = new Sync(this, 4, true, true);
    }

    public void run(double deltaMs) {
        if (sync.stale()) return;

        double beat = sync.basis();
        double pulseWidthFrac = energy.getNormalized() * 3 / 8;
        double swingBeat = TEMath.easeOutPow(beat, energy.getNormalized());
        double pulseHeadFrac = (sync.step() + swingBeat) / 4 * (1 + pulseWidthFrac);
        double pulseTailFrac = pulseHeadFrac - pulseWidthFrac;

        for (LXModel child : model.children) {
            int index = 0;
            for (LXPoint point : child.points) {
                double frac = ((double) index++) / child.points.length;
                colors[point.index] = frac >= pulseTailFrac && frac < pulseHeadFrac ? LXColor.WHITE : LXColor.BLACK;
            }
        }
    }
}
