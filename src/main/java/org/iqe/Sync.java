package org.iqe;

import heronarts.lx.LXComponent;
import heronarts.lx.Tempo;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.parameter.LXParameterListener;
import heronarts.lx.parameter.TriggerParameter;
import heronarts.lx.pattern.LXPattern;

import java.lang.reflect.Method;
import java.util.HashSet;
import java.util.Set;

/**
 * Basically a one-shot / click type of parameter / synchronization system,
 * mappable from Tempo or Hit detect type modulators.
 */
// todo: bulletproof this to act like a click modulator, 1 for one tick 0 all else
public class Sync extends CompoundParameter implements LXParameterListener {
    public final TriggerParameter trigger = new TriggerParameter("trigger");


    private boolean triggering = false;
    // Keep estimate (should be basically exact for uniform / tempo synced signals) of
    // tempo division represented by this triggered sync
    public Tempo.Division division = Tempo.Division.QUARTER;
    private long lastTrigger = -1;
    private long minTriggerWaveDetectDelayMs = 1;

    private int step = 0;
    private Integer staticSteps;
    // We might want multiple patterns to re-use same sync objects?
    private final Set<String> components = new HashSet<>();

    public Sync(LXPattern pattern) {
        this(pattern, null);
    }
    public Sync(LXPattern pattern, Integer staticSteps) {
        super("sync", 0, 1);
        this.staticSteps = staticSteps;
        components.add(pattern.getLabel());
        pattern.getLX().engine.addLoopTask(deltaMs -> detectAndFireTrigger());
        Audio.get().addEndTask(deltaMs -> triggering = false);
        trigger.onTrigger(this::markTriggering);

        // todo: damn, inheritance problems again, verify security manager all platforms
        try {
            Method adder = LXComponent.class.getDeclaredMethod("addParameter", String.class, LXParameter.class);
            adder.setAccessible(true);
            adder.invoke(pattern, "trigger", trigger);

            // shouldn't need this parameter anymore, trigger approach has been working
            // adder.invoke(pattern, "sync", this);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private void detectAndFireTrigger() {
        // Check for peak wave input
        long now = Audio.now();
        if (now - lastTrigger > minTriggerWaveDetectDelayMs && getValue() >= 0.95) {
            markTriggering();
        }

        if (triggering) {
            onSyncTrigger();
        }
    }

    public boolean isTriggering() {
        return triggering;
    }

    private void onSyncTrigger() {
        LOG.debug("Sync onTrigger");
        advance();
        long now = Audio.now();
        if (lastTrigger > 0) {
            Tempo.Division division = Audio.get().closestTempoDivision(now - lastTrigger);
            // todo: Might not want to update this if manual (click or midi/osc message) trigger, but
            //      also don't want to clutter the UI
            if (division != this.division) {
                LOG.info("Sync division {} for {}, prev: {}", this.division, components, division);
                this.division = division;
                // Allow re-triggers with about 2 sixteenth notes tolerance
                minTriggerWaveDetectDelayMs = (long) (Audio.get().period / division.multiplier
                        - 1.8 * (Audio.get().period / Tempo.Division.SIXTEENTH.multiplier));
            }
        }
        lastTrigger = now;
    }

    public int step() {
        return step;
    }

    /* If triggering, increment the current step within bounds and return it */
    public int advance(int steps) {
        return (step = ((isTriggering() ? step + 1 : step) % steps));
    }

    /* Assume number of beats in bar if not explicit */
    public int advance() {
        if (staticSteps != null) return advance(staticSteps);

        double timeSignatureNumerator = Audio.get().lx.engine.tempo.beatsPerMeasure.getValue();
        return advance((int) (division.multiplier * timeSignatureNumerator));
    }

    public void markTriggering() {
        LOG.debug("Sync is marked as triggering");
        this.triggering = true;
    }

    public boolean stale() {
        long now = Audio.now();
        long diff = now - lastTrigger;
        double periodMs = Audio.get().periodOf(division);
        boolean stale = diff > periodMs;
//        if (stale) LOG.info("Sync became stale");
        return stale;
    }

    public double basis() {
        return Audio.get().lx.engine.tempo.getBasis(division);
    }

    @Override
    public void onParameterChanged(LXParameter lxParameter) {
        if (lxParameter.getValue() == 1.0) {
            markTriggering();
        }
    }

    public void setSteps(Integer steps) {
        staticSteps = steps;
    }
}