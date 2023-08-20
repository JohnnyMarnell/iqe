package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.Tempo;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.parameter.BooleanParameter;
import heronarts.lx.pattern.LXPattern;
import heronarts.lx.utils.LXUtils;
import org.iqe.Audio;

import static org.iqe.Audio.basis;

public class MindLikeWaterPattern extends LXPattern {
    final BooleanParameter enabled = new BooleanParameter("running",true);
    public MindLikeWaterPattern(LX lx) {
        super(lx);
        addParameter(enabled);
    }

    @Override
    protected void run(double v) {
        for (LXPoint p : model.points) colors[p.index] = LXColor.CLEAR;
        if (!enabled.getValueb()) return;
//        double radius = basis(Tempo.Division.WHOLE) * 2.;
        double radius = basis(Tempo.Division.QUARTER) * 1.;
        double borderWidth = .2;

        for (LXPoint p : model.points) {
            double xn = p.xn, zn = p.zn;
            if (model.xRange > model.zRange) {
                zn *= model.zRange / model.xRange;
            } else {
                xn *= model.xRange / model.zRange;
            }
            double dist = LXUtils.dist(0., 0., xn, zn);
            if (dist >= radius - borderWidth && dist <= radius + borderWidth) {
                colors[p.index] = LXColor.rgba(255, 255, 255, (int) (1. - Math.abs(radius - dist) / borderWidth * 255));
//                colors[p.index] = LXColor.grayn(1. - Math.abs(radius - dist) / borderWidth);
            }
        }
    }
}
