package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.Tempo;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.pattern.LXPattern;

import java.util.ArrayList;
import java.util.List;

@LXCategory(LXCategory.TEST)
public class HolyTrinitiesPattern extends LXPattern
        implements Tempo.Listener
{
    private LX lx;

    private List<List<Integer>> groups;
    private List<Integer> order;

    public HolyTrinitiesPattern(LX lx) {
        super(lx);
        this.lx = lx;
        lx.engine.tempo.addListener(this);
        initGroupsAndOrders();
    }

    @Override
    protected void run(double deltaMs) {
        // set all points to green
        for (LXPoint p : model.points) {
            colors[p.index] = LXColor.rgba(0, 255, 0, 255);
        }

        // Using current beat, identify group to highlight and highlight them red
        double beat = lx.engine.tempo.getCompositeBasis();
        double div = 1.0; // could be halftime, measure/bar, etc
        int index = ((int) (beat / div)) % order.size(); // get the relative offset into the ordering

        // paint that town red
        for (int fixture : groups.get(order.get(index))) {
            for (LXPoint p : model.children[fixture].points) {
                colors[p.index] = LXColor.rgba(255, 0, 0, 255);
            }
        }
    }

    void initGroupsAndOrders() {
        // build all twelve triangles as groups
        groups = new ArrayList<>();
        int o1, o2;

        // triangles with x-axis-3-strip length bases, pointing z+ up, in near to far order
        o1 = 0; o2 = 0;  groups.add(List.of(33 + o1, 34 + o1, 35 + o1, 45 + o2, 46 + o2, 49 + o2, 50 + o2));
        o1 = 3; o2 = 8;  groups.add(List.of(33 + o1, 34 + o1, 35 + o1, 45 + o2, 46 + o2, 49 + o2, 50 + o2));
        o1 = 6; o2 = 16;  groups.add(List.of(33 + o1, 34 + o1, 35 + o1, 45 + o2, 46 + o2, 49 + o2, 50 + o2));

        // triangles with x-axis-3-strip length bases, pointing z- down, in near to far order
        o1 = 0; o2 = 0;  groups.add(List.of(36 + o1, 37 + o1, 38 + o1, 47 + o2, 48 + o2, 51 + o2, 52 + o2));
        o1 = 3; o2 = 8;  groups.add(List.of(36 + o1, 37 + o1, 38 + o1, 47 + o2, 48 + o2, 51 + o2, 52 + o2));
        o1 = 6; o2 = 16;  groups.add(List.of(36 + o1, 37 + o1, 38 + o1, 47 + o2, 48 + o2, 51 + o2, 52 + o2));

        // triangles with z-axis-3-strip length bases, in 2x near to far order
        o1 = 0; o2 = 0;  groups.add(List.of(15 + o1, 16 + o1, 17 + o1, 45 + o2, 46 + o2, 47 + o2, 48 + o2));
        o1 = 3; o2 = 8;  groups.add(List.of(15 + o1, 16 + o1, 17 + o1, 45 + o2, 46 + o2, 47 + o2, 48 + o2));
        o1 = 6; o2 = 16; groups.add(List.of(15 + o1, 16 + o1, 17 + o1, 45 + o2, 46 + o2, 47 + o2, 48 + o2));

        o1 = 0; o2 = 0;  groups.add(List.of(24 + o1, 25 + o1, 26 + o1, 49 + o2, 50 + o2, 51 + o2, 52 + o2));
        o1 = 3; o2 = 8;  groups.add(List.of(24 + o1, 25 + o1, 26 + o1, 49 + o2, 50 + o2, 51 + o2, 52 + o2));
        o1 = 6; o2 = 16; groups.add(List.of(24 + o1, 25 + o1, 26 + o1, 49 + o2, 50 + o2, 51 + o2, 52 + o2));

        // add the 3 square orderings of its triangles
        int o3;
        this.order = new ArrayList<>();
        o3 = 0; this.order.addAll(List.of(6 + o3, 0 + o3, 9 + o3, 3 + o3));
        o3 = 1; this.order.addAll(List.of(6 + o3, 0 + o3, 9 + o3, 3 + o3));
        o3 = 2; this.order.addAll(List.of(6 + o3, 0 + o3, 9 + o3, 3 + o3));
    }

    @Override
    public void onBeat(Tempo tempo, int beat) {
        System.out.println("beat " + beat + ", " + lx.engine.tempo.getCompositeBasis()
                + " " + model.children[0].tags);
        Tempo.Listener.super.onBeat(tempo, beat);
    }

    @Override
    public void onMeasure(Tempo tempo) {
        System.out.println("measure " + tempo.measure());
        Tempo.Listener.super.onMeasure(tempo);
    }
}