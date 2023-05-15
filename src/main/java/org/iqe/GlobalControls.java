package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.Tempo;
import heronarts.lx.effect.LXEffect;
import heronarts.lx.parameter.BooleanParameter;
import heronarts.lx.parameter.DiscreteParameter;
import heronarts.lx.parameter.TriggerParameter;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * A lot of the finagling and hacky stuff here is because I don't yet know about proper UI
 * and organization. Adding a global effect that I can throw controls into
 */
public class GlobalControls extends LXEffect {
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
    public static final TriggerParameter highIntensity = new TriggerParameter("highIntensity")
            .setDescription("Trigger a high intensity dynamic event");

    public static final TriggerParameter pFire = new TriggerParameter("pFire")
            .setDescription("Trigger a pillar fire event");

    public static final int BASS = 0;
    public static final int TEMPO = 1;

    public GlobalControls(LX lx) {
        super(lx);
        this.label.setValue("Global Controls");
        this.setDescription("Global / default control panel");
        this.addParameter("defaultSyncMode", defaultClick);
        this.addParameter("bassDynamics", bassDynamics);
        this.addParameter("bassBnc", bassBounce);
        this.addParameter("build", build);
        this.addParameter("highIntensity", highIntensity);
        this.addParameter("pFire", pFire);

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
