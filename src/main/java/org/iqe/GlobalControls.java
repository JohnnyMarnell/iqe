package org.iqe;

import heronarts.lx.*;
import heronarts.lx.effect.LXEffect;
import heronarts.lx.parameter.BooleanParameter;
import heronarts.lx.parameter.BoundedParameter;
import heronarts.lx.parameter.DiscreteParameter;
import heronarts.lx.parameter.TriggerParameter;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static org.iqe.LXPluginIQE.INTERNAL;

/**
 * A lot of the finagling and hacky stuff here is because I don't yet know about proper UI
 * and organization. Adding a global effect that I can throw controls into.
 *
 * Update 2025: Never did learn how to properly set this up... I believe the instance was manually
 * added to the .lxp in the GUI (not programmatically). It's visible on Master channel's plugin tab.
 */
@LXCategory(INTERNAL) @LXComponent.Hidden
public class GlobalControls extends LXEffect {
    public static final BoundedParameter speed = new BoundedParameter("speedUp", 0.0, 0.0, 1.0)
            .setDescription("Globally speed up pattern animations, 0 is no speed up");
    public static final List<String> clicks = buildClicks();
    public static final DiscreteParameter defaultClick =
            new DiscreteParameter("syncMode", clicks.toArray(new String[0]))
                    .setDescription("Tempo division (quantize) amount or triggering (e.g. from bass) that default / global setting uses.");
    public static final BooleanParameter bassDynamics = new BooleanParameter("bassDynamics")
            .setDescription("Whether or not overall mood / energy can respond to bass pattern changes (e.g. drop)")
            .setValue(true);
    public static final BooleanParameter bassBounce = new BooleanParameter("bassBnc")
            .setDescription("Toggle global bass bounce mode")
            .setValue(false);

    public static final TriggerParameter build = new TriggerParameter("build")
            .setDescription("Trigger a build up dynamic event");

    public static final TriggerParameter freeBass = new TriggerParameter("freeBass")
            .setDescription("Temporarily allow bass hits unlimited re-triggering");
    public static final TriggerParameter highIntensity = new TriggerParameter("highIntensity")
            .setDescription("Trigger a high intensity dynamic event");

    public static final TriggerParameter pFire = new TriggerParameter("pFire")
            .setDescription("Trigger a pillar fire event");

    public static final TriggerParameter pattern = new TriggerParameter("pattern")
            .setDescription("Cycle next pattern");

    public static final TriggerParameter color = new TriggerParameter("color")
            .setDescription("Cycle next color");

    public static final int BASS = 0;
    public static final int TEMPO = 1;

    public GlobalControls(LX lx) {
        super(lx);
        this.label.setValue("Global Controls");
        this.setDescription("Global / default control panel");
        this.addParameter("speed", speed);
        this.addParameter("defaultSyncMode", defaultClick);
        this.addParameter("bassDynamics", bassDynamics);
        this.addParameter("bassBnc", bassBounce);
        this.addParameter("build", build);
        this.addParameter("freeBass", freeBass);
        this.addParameter("highIntensity", highIntensity);
        this.addParameter("pFire", pFire);
        this.addParameter("pattern", pattern);
        this.addParameter("color", color);

        defaultClick.setValue(clicks.indexOf(Tempo.Division.QUARTER.toString()), true);

        AudioModulators.register(this);
    }

    // Effects have later stage execution it appears, so leverage that!
    @Override
    protected void run(double deltaMs, double dampedAmount) {
        Audio.get().engineLoopEnd(deltaMs);
    }

    private static List<String> buildClicks() {
        List<String> clicks = new ArrayList<>();
        clicks.add(BASS, "BASS");
        Arrays.stream(Tempo.Division.values()).forEach(div -> clicks.add(div.toString()));
        return clicks;
    }
}
