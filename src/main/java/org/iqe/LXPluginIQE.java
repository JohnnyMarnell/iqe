package org.iqe;

import heronarts.lx.*;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.modulation.LXModulationEngine;
import heronarts.lx.modulator.LXModulator;
import heronarts.lx.modulator.LXWaveshape;
import heronarts.lx.modulator.VariableLFO;
import heronarts.lx.osc.LXOscComponent;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.pattern.LXPattern;

import java.util.*;
import java.util.function.Function;

public class LXPluginIQE implements LXPlugin {
    protected LX lx;

    @Override
    public void dispose() {
        LXPlugin.super.dispose();
    }

    @Override
    public void initialize(LX lx) {
        this.lx = lx;
        Audio.initialize(lx);
        AudioModulators.initialize(lx);
        lx.registry.addPattern(ZipStripPattern.class);
        lx.registry.addPattern(HolyTrinitiesPattern.class);
        lx.registry.addPattern(PillarFirePattern.class);
        lx.registry.addPattern(BassBreathPattern.class);

        // todo: can I loop back osc query message?
        lx.addProjectListener((file, change) -> {
            if (change == LX.ProjectListener.Change.OPEN) {
                LOG.info("Project open");
                oscQueryAll(lx);
            }
        });
    }

    // todo: can I loop back osc query message?
    public static void oscQueryAll(LX lx) {
        int index = 1;
        LXComponent component;
        Set<Integer> visited = new HashSet<>();
        while ((component = lx.getComponent(index)) != null) {
            oscQuery(visited, lx, component);
            index++;
        }
    }

    // todo: can I loop back osc query message?
    public static void oscQuery(Set<Integer> visited, LX lx, LXComponent component) {
        if (!visited.contains(component.getId())) {
            visited.add(component.getId());
            component.getParameters().forEach(lx.engine.osc::sendParameter);
            if (component instanceof LXModulationEngine) {
                ((LXModulationEngine) component).getModulators().forEach(m -> oscQuery(visited, lx, m));
            }
            component.children.values().forEach(c -> oscQuery(visited, lx, component));
        }
    }
}
