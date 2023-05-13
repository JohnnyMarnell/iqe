package org.iqe;


import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.Tempo;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import heronarts.lx.parameter.BooleanParameter;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.DiscreteParameter;
import heronarts.lx.parameter.TriggerParameter;
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
    public final TriggerParameter trigger =
            new TriggerParameter("trigger")
                    .setDescription("Manual (or wire modulator) for pulse triggering");
    public final CompoundParameter tmp =
            new CompoundParameter("tmp")
                    .setDescription("Test test");

    private int step = 0;

    public ZipStripPattern(LX lx) {
        super(lx);
        addParameter("energy", energy);
        addParameter("trigger", trigger);
        addParameter("tmp2", new BooleanParameter("tmp1"));
        addParameter("tmp", tmp);
        addParameter("tmp3", new DiscreteParameter("tmp3", 1));
    }

    public void run(double deltaMs) {
//        step = wtf.getValue() == 1.0f ? (step + 1) % 4 : step;
//        step = AudioModulators.quarterClick.click() ? (step + 1) % 4 : step;
//        double beat = AudioModulators.quarter.getBasis();
//        double beat = Audio.get().basis(Tempo.Division.QUARTER);
        step = Audio.get().click(Tempo.Division.EIGHTH_DOT) ? (step + 1) % 4 : step;
        double beat = Audio.get().basis(Tempo.Division.EIGHTH_DOT);

        double pulseWidthFrac = energy.getNormalized() * 3 / 8;
        double swingBeat = TEMath.easeOutPow(beat, energy.getNormalized());
        double pulseHeadFrac = (step + swingBeat) / 4 * (1 + pulseWidthFrac);
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
