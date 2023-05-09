package org.iqe;

import heronarts.lx.*;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.modulation.LXModulationEngine;
import heronarts.lx.osc.LXOscComponent;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.pattern.LXPattern;

import java.util.*;

public class LXPluginIQE implements LXPlugin {
    protected LX lx;

    @Override
    public void dispose() {
        LXPlugin.super.dispose();
    }

    @Override
    public void initialize(LX lx) {
        this.lx = lx;
        lx.registry.addPattern(HolyTrinitiesPattern.class);
        lx.registry.addPattern(BassBreathPattern.class);

        // IMHO it's great this exists, and should be made public and happen by default on project load
        lx.addProjectListener((file, change) -> {
            if (change == LX.ProjectListener.Change.OPEN) {
                oscQueryAll(lx);
            }
        });
    }

    // IMHO it's great this exists, and should be made public and happen by default on project load
    public static void oscQueryAll(LX lx) {
        int index = 1;
        LXComponent component;
        Set<Integer> visited = new HashSet<>();
        while ((component = lx.getComponent(index)) != null) {
            oscQuery(visited, lx, component);
            index++;
        }
    }

    // IMHO it's great this exists, and should be made public and happen by default on project load
    public static void oscQuery(Set<Integer> visited, LX lx, LXComponent component) {
        if (!visited.contains(component.getId())) {
            System.out.println("sigh " + component.getId() + " " + component.getLabel() + " " + component.getClass());
            visited.add(component.getId());
            component.getParameters().forEach(lx.engine.osc::sendParameter);
            if (component instanceof LXModulationEngine) {
                ((LXModulationEngine) component).getModulators().forEach(m -> oscQuery(visited, lx, m));
            }
            component.children.values().forEach(c -> oscQuery(visited, lx, component));
        }
    }
}
