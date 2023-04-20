package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.LXPlugin;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.pattern.LXPattern;

public class LXPluginIQE implements LXPlugin {

    @LXCategory(LXCategory.TEST)
    public static class TestIQEPattern extends LXPattern {

        public TestIQEPattern(LX lx) {
            super(lx);
            System.out.println("*** LXP Pattern ctr");
        }

        @Override
        protected void run(double deltaMs) {
//            System.out.println("*** tick " + deltaMs);
            for (LXPoint p : model.points) {
                colors[p.index] = LXColor.hsb(240, 100, 100);
            }
        }
    }

    @Override
    public void dispose() {
        LXPlugin.super.dispose();
    }

    @Override
    public void initialize(LX lx) {
        System.out.println("*** LXP init");
        lx.registry.addPattern(TestIQEPattern.class);
        lx.registry.addPattern(BassBreathPattern.class);
    }
}
