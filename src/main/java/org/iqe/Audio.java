package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.Tempo;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.utils.LXUtils;
import titanicsend.TEAudioPattern;
import titanicsend.TEMath;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static java.lang.Math.PI;
import static java.lang.Math.sin;

/**
 * Main Audio engine class and logic.
 * todo: Also has become a bit more than that, entry point to a lot of classes, change that?
 */

// todo: decide on Singleton-ify
// todo: How do I "find" components in LX project / universe?
// todo: add to audio engine (and modulators? tho not sure I could "script" what I want thru UI)
//     a bass drop out and re-enter by counting hits
public class Audio implements Tempo.Listener {

    // todo: barves.
    private static Audio instance = null;

    public final LX lx;
    public final OscBridge osc;
    public final Orchestrator orchestrator;

    public final TEAudioPattern teEngine;
    public long lastBassHit = 0;

    public double bpm = 120.0d;
    /* period is millis of 1 beat */
    public double period = 60.0d / bpm * 1_000d;

    public interface Task { void run(double deltaMs); }
    private final List<Task> startTasks = new ArrayList<>();
    private final List<Task> endTasks = new ArrayList<>();
    final TempoClick[] clicks = new TempoClick[Tempo.Division.values().length];

    private Audio(LX lx) {
        this.lx = lx;
        osc = new OscBridge(lx);
        orchestrator = new Orchestrator(lx, osc);

        teEngine = new TEAudioPattern(lx);

        for (Tempo.Division division : Tempo.Division.values()) {
            this.clicks[division.ordinal()] = new TempoClick(lx, division);
        }

        lx.engine.tempo.addListener(this);
        lx.engine.tempo.tap.addListener(this::onTap, true);
        lx.engine.tempo.nudgeUp.addListener(this::onNudgeUp, true);
        lx.engine.tempo.nudgeDown.addListener(this::onNudgeDown, true);
        lx.engine.tempo.period.addListener(this::onPeriod, true);
        lx.engine.tempo.bpm.addListener(this::onBpm, true);
    }

    public Tempo.Division closestTempoDivision(double periodMillis) {
        return Arrays.stream(Tempo.Division.values())
                .min((lhs, rhs) -> {
                    double lDiff = Math.abs(periodOf(lhs) - periodMillis);
                    double rDiff = Math.abs(periodOf(rhs) - periodMillis);
                    return (int) (lDiff - rDiff);
                }).orElseThrow();
    }

    /** I think this is tempo sync + locked clicking */
    public static class TempoClick {
        private final LX lx;
        public int clicks = 0;
        public boolean isOn = false;
        public Tempo.Division division;

        public TempoClick(LX lx, Tempo.Division division) {
            this.lx = lx;
            this.division = division;
        }

        void tick() {
            int clicks = ((int) lx.engine.tempo.getBasis(division, false)) + 1;
            if (clicks != this.clicks) {
                isOn = true;
                this.clicks = clicks;
            } else {
                isOn = false;
            }
        }
    }

    public void run(double deltaMs) {
        Arrays.stream(clicks).parallel().forEach(TempoClick::tick);

        long now = lx.engine.nowMillis;
        teEngine.computeAudio(deltaMs);

        // Some example metrics found in TE
        // I see this in Heart + Art Standards patterns
        double energyNormalized = .7;
        double scaledTrebleRatio = LXUtils.clamp(
                (teEngine.getTrebleRatio() - .5) / (1.01 - energyNormalized) / 6 -
                        .2 + energyNormalized / 2,
                0, 1);
        double squaredScaledTrebleRatio = Math.pow(scaledTrebleRatio, 2);
        energyNormalized = .6;
        double bassHeightNormalized = (teEngine.getBassRatio() - .5) / (1.01 - energyNormalized) / 3 - .2;
        double beats = lx.engine.tempo.getCompositeBasis();
        double sinPhaseBeat = .5 * sin(PI * beats) + .5;
        // actually, this should use time sig right? and be "8 'bars / measures'"?
        double phrase = beats / 32 % 1.0D;
        double beatsPerMeasure = lx.engine.tempo.beatsPerMeasure.getValue();
        double measure = (beats % beatsPerMeasure) / beatsPerMeasure;
        // interesting mention of swing in Tempo Reactive, idk if I agree with this calc / def
        double swingBeat = TEMath.easeOutPow(basis(Tempo.Division.QUARTER), energyNormalized);

        // all the basis obviously... (especially quarter, half, eighth, whole)
        // expose all in teEngine
        // maybe the rotation / spin / rotor stuff? tho I don't yet see how the other basis parameters * 2pi, maybe
        //   with built-in damping used, wouldn't get you there already?

        if (bassHit()) {
            double bpm = 0;
            if (lastBassHit != 0) {
                double secondsPerBeat = (now - lastBassHit) / 1_000.0d;
                double beatsPerSecond = 1.0d / secondsPerBeat;
                bpm = beatsPerSecond * 60.0d;
            }
            lastBassHit = now;
            LOG.debug("Bass hit detected");
            LX.log("BASS HIT! High varying implied bpm: " + bpm);
        }

        for (int i = startTasks.size() - 1; i >= 0; i--) {
            startTasks.get(i).run(deltaMs);
        }
    }

    public void addStartTask(Task task) {
        startTasks.add(task);
    }

    public void addEndTask(Task task) {
        endTasks.add(task);
    }

    public void removeStartTask(Task task) {
        startTasks.remove(task);
    }

    public void engineLoop(double deltaMs) {
        LOG.debug("LX Engine loop task, post global modulators");
    }

    public void engineLoopEnd(double deltaMs) {
        LOG.debug("Last phase, Master Audio Effect space");
        endTasks.stream().parallel().forEach(task -> task.run(deltaMs));
    }
    public boolean click(Tempo.Division division) {
        return clicks[division.ordinal()].isOn;
    }

    public double basis(Tempo.Division division) {
        return lx.engine.tempo.getBasis(division);
    }

    public static double periodOf(Tempo.Division division) {
        return divisionAppliedToPeriod(Audio.get().period, division);
    }

    public static double divisionAppliedToPeriod(double periodMs, Tempo.Division division) {
        return periodMs / division.multiplier;
    }

    public boolean bassHit() {
        return teEngine.bassHit();
    }

    @Override
    public void onBeat(Tempo tempo, int beat) {
        Tempo.Listener.super.onBeat(tempo, beat);
    }

    @Override
    public void onMeasure(Tempo tempo) {
        Tempo.Listener.super.onMeasure(tempo);
    }

    public void onBpm(LXParameter bpm) {
        this.bpm = bpm.getValue();
        LOG.debug("Tempo bpm changed");
        LOG.info("Tempo BPM: {}", this.bpm);
    }

    public void onPeriod(LXParameter period) {
        this.period = period.getValue();
        updateFromPeriod();
        LOG.debug("Tempo period changed");
        LOG.info("Tempo period (ms of 1 beat): {}", this.period);
    }

    private void updateFromPeriod() {
        // Allow the beat detect to only trigger as fast as one beat
        teEngine.bassRetriggerMs = 15./16 * divisionAppliedToPeriod(period, Tempo.Division.QUARTER);
    }

    // Any NA near beers brah?
    public void onTap(LXParameter tap) {

    }

    public void onNudgeUp(LXParameter nudgeUp) {

    }

    public void onNudgeDown(LXParameter nudgeDown) {

    }

    public static long now() {
        return instance.lx.engine.nowMillis;
    }
    public static Audio get() {
        return instance;
    }

    public static void initialize(LX lx) {
        if (instance != null) throw new IllegalStateException("HighlanderException, there can only be one, "
                    + "who would've ever thought static singletons were a bad idea...");
        instance = new Audio(lx);
    }
}
