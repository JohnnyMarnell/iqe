package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.Tempo;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.parameter.BooleanParameter;
import heronarts.lx.parameter.EnumParameter;
import heronarts.lx.pattern.LXPattern;

import java.util.ArrayList;
import java.util.List;

@LXCategory(LXCategory.TEST)
public class HolyTrinitiesPattern extends LXPattern
{
    public static final BooleanParameter bass = new BooleanParameter("bassOn", false);
    public static final EnumParameter<Tempo.Division> division = new EnumParameter<>("tdiv", Tempo.Division.QUARTER);

    private int index;
    private List<List<Integer>> groups;
    private List<Integer> order;

    public HolyTrinitiesPattern(LX lx) {
        super(lx);
        this.index = 0;
        addParameter("bassOn", bass);
        addParameter("tdiv", division);
        initGroupsAndOrders();
    }

    public int nextIndex() {
        boolean advance = bass.isOn() ? AudioModulators.bootsHit.isOn() : Audio.get().click(division.getEnum());
        return advance ? index + 1 : index;
    }

    @Override
    protected void run(double deltaMs) {
        for (LXPoint p : model.points) {
            colors[p.index] = LXColor.rgba(150, 150, 150, 255);
        }

        this.index = nextIndex() % order.size();

        // highlight group
        for (int fixture : groups.get(order.get(index))) {
            for (LXPoint p : model.children[fixture].points) {
                colors[p.index] = LXColor.rgba(255, 255, 255, 255);
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
}