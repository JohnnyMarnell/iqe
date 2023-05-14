package org.iqe;

import heronarts.lx.model.LXPoint;
import heronarts.lx.pattern.LXPattern;

import java.util.Arrays;
import java.util.function.Function;
import java.util.stream.Stream;

public class Geometry {
    public static Stream<LXPoint> points(LXPattern pattern) {
        return Arrays.stream(pattern.getModel().points);
    }

    public static Stream<LXPoint> childPoints(LXPattern pattern, int index) {
        return Arrays.stream(pattern.getModel().children[index].points);
    }

    public static Stream<LXPoint> colorize(LXPattern pattern, Function<LXPoint, Integer> colorizer) {
        points(pattern).forEach(point -> pattern.getColors()[point.index] = colorizer.apply(point));
        return points(pattern);
    }
}
