package org.iqe;

import heronarts.lx.*;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.pattern.LXPattern;

import java.util.ArrayList;
import java.util.List;

public class LXPluginIQE implements LXPlugin {

    @Override
    public void dispose() {
        LXPlugin.super.dispose();
    }

    @Override
    public void initialize(LX lx) {
        System.out.println("*** LXP init");
        lx.registry.addPattern(HolyTrinitiesPattern.class);
        lx.registry.addPattern(BassBreathPattern.class);
    }
}
