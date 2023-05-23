package org.iqe;

import heronarts.lx.LXComponent;
import heronarts.lx.Tempo;
import heronarts.lx.parameter.*;
import heronarts.lx.pattern.LXPattern;

import java.lang.reflect.Method;
import java.util.HashSet;
import java.util.Set;

import static org.iqe.Audio.*;
import static org.iqe.AudioModulators.funcParam;

/**
 * Basically a one-shot / click type of parameter / synchronization system,
 * mappable from Tempo or Hit detect type modulators.
 *
 * Meant to abstract away sync and timing, so patterns are easier to write,
 * and control / interact with / choreograph.
 */
// todo: Allow momentary button behavior and firing (e.g. trigger button held, for "fire" effect especially)
public class Sync extends CompoundParameter implements LXParameterListener {
    public final TriggerParameter trigger = new TriggerParameter("trigger");


    private boolean triggering = false;
    // Keep estimate (should be basically exact for uniform / tempo synced signals) of
    // tempo division represented by this triggered sync
    public Tempo.Division division = Tempo.Division.QUARTER;
    private long lastTrigger = -1;
    private long minTriggerWaveDetectDelayMs = 1;
    private boolean tempoLock = true;
    private boolean variableDivision = true;

    private int step = 0;
    private Integer staticSteps;
    // We might want multiple patterns to re-use same sync objects?
    private final Set<String> components = new HashSet<>();

    public final FunctionalParameter periodMs;

    // todo: Builder pattern, easy constructors
    // todo: Use LXParameters, and probably functional, so it's up to date and better controllable
    // todo: Deactive / don't fire when pattern is not active
    public Sync(LXPattern pattern) {
        this(pattern, null, true, true);
    }
    public Sync(LXPattern pattern, Integer staticSteps, boolean tempoLock, boolean variableDivision) {
        super("sync", 0, 1);
        this.staticSteps = staticSteps;
        this.tempoLock = tempoLock;
        this.variableDivision = variableDivision;
        this.periodMs = funcParam("periodMs", () -> periodOf(division));

        components.add(pattern.getLabel());
        // todo: unify these, static, one forever task
        pattern.getLX().engine.addLoopTask(deltaMs -> detectAndFireTrigger());
        Audio.get().addEndTask(deltaMs -> triggering = false);
        trigger.onTrigger(this::markTriggering);

        // todo: damn, inheritance problems again, verify security manager all platforms
        try {
            Method adder = LXComponent.class.getDeclaredMethod("addParameter", String.class, LXParameter.class);
            adder.setAccessible(true);
            adder.invoke(pattern, "syncTrigger", trigger);

            // shouldn't need this parameter anymore, trigger approach has been working
            // adder.invoke(pattern, "sync", this);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private void detectAndFireTrigger() {
        // Allow for checking a wave signal as well, try to detect cycle
        //   (only if this Sync's compound parameter "sync" is exposed and being driven. I think
        //    I prefer the trigger approach, which is currently only in use)
        if (!triggering) {
            long now = Audio.now();
            if (now - lastTrigger > minTriggerWaveDetectDelayMs && getValue() > 0 && getValue() <= 0.05) {
                markTriggering();
            }
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
        double diff = now - lastTrigger;

        if (lastTrigger > 0 && variableDivision) {
            Tempo.Division division = Audio.get().closestTempoDivision(diff);
            // todo: Might not want to update this if manually triggered (click or midi/osc message), but
            //      also don't want to clutter the UI
            if (division != this.division) {
                LOG.info("Sync division {} for {}, prev: {}", this.division, components, division);
                this.division = division;
                // Allow re-triggers with about 2 sixteenth notes tolerance
                minTriggerWaveDetectDelayMs = (long) (period() / division.multiplier
                        - 1.8 * (period() / Tempo.Division.SIXTEENTH.multiplier));
            }
        }
        lastTrigger = now;
    }

    public int step() {
        return step(false);
    }

    public int step(boolean mod) {
        return mod ? step % stepsSize() : step;
    }

    /* Assume number of beats in bar if not explicit */
    public int stepsSize() {
        // todo: this is probably wrong?
        return staticSteps != null ? staticSteps : (int) Math.ceil(beatsInBar(division));
    }

    public int advance() {
        return ++step;
    }

    public void markTriggering() {
        LOG.debug("Sync is marked as triggering");
        this.triggering = true;
    }

    // todo: yikers island...
    //      maybe I should add more controls, like manual trigger + quantize select, including: time divisions obviously,
    //      whatever Global is at (and changes to), bass, infer from triggers (kind of like tap tempo?)
    public boolean stale() {
        return tempoLock ? Audio.now() - lastTrigger > Audio.periodOf(Tempo.Division.WHOLE) : basis() >= 1.;
    }

    public double basis() {
        return tempoLock ? Audio.tempo().getBasis(division) : (Audio.now() - lastTrigger) / Audio.periodOf(division);
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