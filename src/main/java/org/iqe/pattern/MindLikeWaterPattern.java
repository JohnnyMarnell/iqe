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
import static org.iqe.Audio.totalBasis;

public class MindLikeWaterPattern extends LXPattern {
    final BooleanParameter enabled = new BooleanParameter("running",true);

    public static final double[][] ORIGINS = new double[][] {
            new double[] { 0., 0. },
            new double[] { 1., 0. },
            new double[] { 0., 1. },
            new double[] { 1., 1. },
    };
    public MindLikeWaterPattern(LX lx) {
        super(lx);
        addParameter(enabled);
    }

    @Override
    protected void run(double v) {
        for (LXPoint p : model.points) colors[p.index] = LXColor.CLEAR;
        if (!enabled.getValueb()) return;
        Tempo.Division div = Tempo.Division.WHOLE;
        double radius = basis(div) * 1.;
        double borderWidth = .2;

        double[] origin = ORIGINS[((int) Math.floor(totalBasis(div))) % ORIGINS.length];

        for (LXPoint p : model.points) {
            double xn = p.xn, zn = p.zn;
            if (model.xRange > model.zRange) {
                zn *= model.zRange / model.xRange;
            } else {
                xn *= model.xRange / model.zRange;
            }
            double dist = LXUtils.dist(origin[0], origin[1], xn, zn);
            if (dist >= radius - borderWidth && dist <= radius + borderWidth) {
                colors[p.index] = LXColor.rgba(255, 255, 255, (int) (1. - Math.abs(radius - dist) / borderWidth * 255));
//                colors[p.index] = LXColor.grayn(1. - Math.abs(radius - dist) / borderWidth);
            }
        }
    }

    protected void runWtf(double v) {
        for (LXPoint p : model.points) colors[p.index] = LXColor.CLEAR;
        if (!enabled.getValueb()) return;

//        double radius = basis(Tempo.Division.WHOLE) * 2.;
//        double radius = basis(Tempo.Division.QUARTER) * 1.;

        double multiplier = 1.;
        Tempo.Division div = Tempo.Division.HALF;
//        Tempo.Division div = Tempo.Division.QUARTER;
        double basis = basis(div);
        if (basis <= 0.0001d) return;
        double radius = basis * multiplier;
        double borderWidth = .2;
        double[] origin = ORIGINS[((int) Math.floor(totalBasis(div))) % ORIGINS.length];
//        double origin[] = ORIGINS[0];


        double radiusRangeStart = radius - borderWidth;
        double radiusRangeEnd = radius + borderWidth;
        double radiusRange = radiusRangeEnd - radiusRangeStart;

        for (LXPoint p : model.points) {
            double xn = p.xn, zn = p.zn;
            if (model.xRange > model.zRange) {
                zn *= model.zRange / model.xRange;
            } else {
                xn *= model.xRange / model.zRange;
            }
            double dist = LXUtils.dist(origin[0], origin[1], xn, zn);
            double radiusFrac = (dist - radiusRangeStart) / radiusRange;

            double alpha;
            if (radiusFrac < 0 || radiusFrac > 1.) continue;
            else if (dist < .2) alpha = radiusFrac / .2 * 1.;
            else if (dist < .8) alpha = 1.;
            else alpha = (radiusFrac - .8) / .2 * 1.;

            alpha *= basis < .9 ? 1 : (1. - (basis - .9)) / .1;

            colors[p.index] = LXColor.rgba(255, 255, 255, (int) alpha);
        }
    }
}
