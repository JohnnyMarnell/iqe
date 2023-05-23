package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.color.LXColor;
import heronarts.lx.pattern.LXPattern;
import org.iqe.Sync;

import java.util.ArrayList;
import java.util.List;

import static org.iqe.Geometry.*;

@LXCategory(LXCategory.TEST)
public class HolyTrinitiesPattern extends LXPattern
{
    public final Sync sync;
    private List<List<Integer>> groups;
    private List<Integer> order;

    public HolyTrinitiesPattern(LX lx) {
        super(lx);
        initGroupsAndOrders();
        this.sync = new Sync(this, order.size(), true, true);
    }

    @Override
    protected void run(double deltaMs) {
        // First dim all colors on all points
        colorize(this, p -> LXColor.grayn(0.60));

        // Then highlight active group
        int highlightAlpha = LXColor.WHITE;
        List<Integer> stripIndexes = groups.get(order.get(sync.step(true)));
        stripIndexes.stream()
                .flatMap(stripIndex -> childPoints(this, stripIndex))
                .forEach(point -> colors[point.index] = highlightAlpha);
    }

    // todo: make this configurable, and more than triangles
    void initGroupsAndOrders() {
        // build all twelve triangles as groups
        groups = new ArrayList<>();
        int o1, o2;

        // triangles with x-axis-3-strip length bases, pointing z+ up, in near to far order
        o1 = 0; o2 = 0;  groups.add(List.of(39 + o1, 40 + o1, 41 + o1, 51 + o2, 52 + o2, 55 + o2, 56 + o2));
        o1 = 3; o2 = 8;  groups.add(List.of(39 + o1, 40 + o1, 41 + o1, 51 + o2, 52 + o2, 55 + o2, 56 + o2));
        o1 = 6; o2 = 16; groups.add(List.of(39 + o1, 40 + o1, 41 + o1, 51 + o2, 52 + o2, 55 + o2, 56 + o2));

        // triangles with x-axis-3-strip length bases, pointing z- down, in near to far order
        o1 = 0; o2 = 0;  groups.add(List.of(42 + o1, 43 + o1, 44 + o1, 53 + o2, 54 + o2, 57 + o2, 58 + o2));
        o1 = 3; o2 = 8;  groups.add(List.of(42 + o1, 43 + o1, 44 + o1, 53 + o2, 54 + o2, 57 + o2, 58 + o2));
        o1 = 6; o2 = 16; groups.add(List.of(42 + o1, 43 + o1, 44 + o1, 53 + o2, 54 + o2, 57 + o2, 58 + o2));

        // triangles with z-axis-3-strip length bases, in 2x near to far order
        o1 = 0; o2 = 0;  groups.add(List.of(21 + o1, 22 + o1, 23 + o1, 51 + o2, 52 + o2, 53 + o2, 54 + o2));
        o1 = 3; o2 = 8;  groups.add(List.of(21 + o1, 22 + o1, 23 + o1, 51 + o2, 52 + o2, 53 + o2, 54 + o2));
        o1 = 6; o2 = 16; groups.add(List.of(21 + o1, 22 + o1, 23 + o1, 51 + o2, 52 + o2, 53 + o2, 54 + o2));

        o1 = 0; o2 = 0;  groups.add(List.of(30 + o1, 31 + o1, 32 + o1, 55 + o2, 56 + o2, 57 + o2, 58 + o2));
        o1 = 3; o2 = 8;  groups.add(List.of(30 + o1, 31 + o1, 32 + o1, 55 + o2, 56 + o2, 57 + o2, 58 + o2));
        o1 = 6; o2 = 16; groups.add(List.of(30 + o1, 31 + o1, 32 + o1, 55 + o2, 56 + o2, 57 + o2, 58 + o2));

        // add the 3 square orderings of its triangles
        int o3;
        this.order = new ArrayList<>();
        o3 = 0; this.order.addAll(List.of(6 + o3, 0 + o3, 9 + o3, 3 + o3));
        o3 = 1; this.order.addAll(List.of(6 + o3, 0 + o3, 9 + o3, 3 + o3));
        o3 = 2; this.order.addAll(List.of(6 + o3, 0 + o3, 9 + o3, 3 + o3));
    }
}