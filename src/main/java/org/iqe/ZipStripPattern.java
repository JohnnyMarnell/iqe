package org.iqe;


import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.Tempo;
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

    public ZipStripPattern(LX lx) {
        super(lx);
        addParameter("energy", energy);
    }

    public void run(double deltaMs) {
        // todo: Most of this goes away and get one value from Audio
        double measure = Audio.get().basis(Tempo.Division.WHOLE);
        int beatInMeasure = (int) (measure * 4);
        double beat = lx.engine.tempo.basis();
        double pulseWidthFrac = energy.getNormalized() * 3 / 8;
        double swingBeat = TEMath.easeOutPow(beat, energy.getNormalized());
        double pulseHeadFrac = (beatInMeasure + swingBeat) / 4 * (1 + pulseWidthFrac);
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
