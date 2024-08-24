package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.LXComponent;
import heronarts.lx.Tempo;
import heronarts.lx.audio.GraphicMeter;
import heronarts.lx.effect.LXEffect;
import heronarts.lx.parameter.BooleanParameter;
import heronarts.lx.parameter.LXListenableParameter;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.parameter.LXParameterListener;
import heronarts.lx.utils.LXUtils;
import titanicsend.TEAudioPattern;
import titanicsend.TEMath;

import java.util.*;

import static java.lang.Math.PI;
import static java.lang.Math.sin;
import static org.iqe.AudioModulators.FuncParam;
import static org.iqe.AudioModulators.register;
import static org.iqe.LXPluginIQE.INTERNAL;

/**
 * <p>
 * Main Audio engine class and logic.
 *
 * </p>
 * todo: Also has become a bit more than that, entry point to a lot of classes, change that?
 */

// todo: decide on Singleton-ify
// todo: How do I "find" components in LX project / universe?
// todo: add to audio engine (and modulators? tho not sure I could "script" what I want thru UI)
//     a bass drop out and re-enter by counting hits
public class Audio implements Tempo.Listener {

    // todo: barves.
    private static Audio instance = null;

    private static LX lx;
    private static Tempo tempo;
    public final OscBridge osc;
    public final Orchestrator orchestrator;

    public final TEAudioPattern teEngine;
    public long lastBassHit = 0;

    public interface Task { void run(double deltaMs); }
    private final List<Task> startTasks = new ArrayList<>();
    private final List<Task> endTasks = new ArrayList<>();
    final TempoClick[] clicks = new TempoClick[Tempo.Division.values().length];

    private final Map<LXListenableParameter, LXParameterListener> listeners = new HashMap<>();

    public static final BooleanParameter limitBassRetrigger = new BooleanParameter("limitBassRetrigger", true)
            .setDescription("Whether to suppress bass hit detection by frequency");

    private Audio() {
        osc = new OscBridge(lx);
        orchestrator = new Orchestrator(lx, osc);

        for (Tempo.Division division : Tempo.Division.values()) {
            this.clicks[division.ordinal()] = new TempoClick(division);
        }

        tempo.addListener(this);
        listeners.put(tempo.tap, this::onTap);
        listeners.put(tempo.tap, this::onTap);
        listeners.put(tempo.nudgeUp, this::onNudgeUp);
        listeners.put(tempo.nudgeDown, this::onNudgeDown);
        listeners.put(tempo.period, this::onPeriod);
        listeners.put(tempo.bpm, this::onBpm);
        listeners.forEach(LXListenableParameter::addListener);


        teEngine = new TEAudioPattern(lx);
        // When limiting bass re-triggers, do it by 94% of a beat
        teEngine.bassRetriggerMs = new FuncParam("bassRetriggerMs",
                () -> !limitBassRetrigger.getValueb() ? 0. : 15./16 * periodOf(Tempo.Division.QUARTER));
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
        public int clicks = 0;
        public boolean isOn = false;
        public Tempo.Division division;

        public TempoClick(Tempo.Division division) {
            this.division = division;
        }

        void tick() {
            int clicks = ((int) totalBasis(division)) + 1;
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
        double beats = tempo.getCompositeBasis();
        double sinPhaseBeat = .5 * sin(PI * beats) + .5;
        // actually, this should use time sig right? and be "8 'bars / measures'"?
        double phrase = beats / 32 % 1.0D;
        double beatsPerMeasure = tempo.beatsPerMeasure.getValue();
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
            LOG.debug("BASS HIT! High varying implied bpm: " + bpm);
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

    public static double basis(Tempo.Division division) {
        return tempo.getBasis(division);
    }
    public static double totalBasis(Tempo.Division division) {
        return tempo.getBasis(division, false);
    }

    public static double period() {
        return tempo.period.getValue();
    }

    public static double beatsInBar() {
        return tempo.beatsPerMeasure.getValuei();
    }

    public static double beatsInBar(Tempo.Division division) {
        return division.multiplier * beatsInBar();
    }

//    public static double basis(Tempo.Division division) {
//        return tempo.getBasis(division);
//    }
    public static double periodOf(Tempo.Division division) {
        return divisionAppliedToPeriod(period(), division);
    }

    public static double bar() {
        return periodOf(Tempo.Division.WHOLE);
    }

    public static double bars(int numBars) {
        return numBars * bar();
    }

    public static double divisionAppliedToPeriod(double periodMs, Tempo.Division division) {
        return periodMs / division.multiplier;
    }

    public boolean bassHit() {
        return teEngine.bassHit();
    }

    public GraphicMeter graphicMeter() {
        return teEngine.eq;
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
        LOG.debug("Tempo bpm changed");
        LOG.info("Tempo BPM: {}", bpm);
    }

    public void onPeriod(LXParameter period) {
        LOG.debug("Tempo period changed");
        LOG.info("Tempo period (ms of 1 beat): {}", period);
    }

    // Any NA near beers brah?
    public void onTap(LXParameter tap) {

    }

    public void onNudgeUp(LXParameter nudgeUp) {

    }

    public void onNudgeDown(LXParameter nudgeDown) {

    }

    public static long now() {
        return lx.engine.nowMillis;
    }
    public static Audio get() {
        return instance;
    }
    public static LX lx() {
        return lx;
    }
    public static Tempo tempo() {
        return tempo;
    }

    /** Just a place to register select parameters, so they get OSC read/write capability */
    public static class GlobalParams extends LXEffect {

        public GlobalParams(LX lx) {
            super(lx);
            addParameter(limitBassRetrigger.getLabel(), limitBassRetrigger);
            register(this);
        }

        @Override
        protected void run(double v, double v1) {

        }
    }
    @LXCategory(INTERNAL) @LXComponent.Hidden
    public static class NO_TOUCHY extends GlobalParams { public NO_TOUCHY(LX lx) { super(lx); } }

    void dispose() {
        tempo.removeListener(this);
        listeners.forEach(LXListenableParameter::removeListener);

        orchestrator.dispose();
        osc.dispose();
    }

    public static void initialize(LX lx) {
        if (instance != null) throw new IllegalStateException("HighlanderException, there can only be one, "
                    + "who would've ever thought static singletons were a bad idea...");
        Audio.lx = lx;
        Audio.tempo = Audio.lx.engine.tempo;
        instance = new Audio();
    }
}
