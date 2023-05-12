package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.Tempo;
import heronarts.lx.effect.LXEffect;
import heronarts.lx.modulator.Click;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.utils.LXUtils;

import java.util.Arrays;

import static java.lang.Math.PI;
import static java.lang.Math.sin;

// todo: decide on Singleton-ify
// todo: Add global modulators for patterns to switch between, with default division as well
// todo: Maybe multiple clicks is a bad idea, could detect clicks based on basis changes, if they ever
//          decrease, assume click?
public class Audio extends LXEffect implements Tempo.Listener {

    // todo: barves.
    private static Audio instance = null;
    private final TEAudioPattern teEngine;
    private long lastBassHit = 0;

    double bpm = 120.0d;
    /* period is millis of 1 beat */
    double period = 60.0d / bpm * 1_000d;

    private final Click beat;
    private final Click bar;
    private final Click[] click = new Click[Tempo.Division.values().length];

    /** LX seems inheritance heavy, so try using a Global, always on effect */
    public Audio(LX lx) {
        super(lx);
        if (instance != null) throw new IllegalStateException("Highlander Exception, there can only be one.");
        Audio.instance = this;

        teEngine = new TEAudioPattern(lx);

        for (Tempo.Division division : Tempo.Division.values()) {
            this.click[division.ordinal()] = buildClick(division);
        }
        this.beat = click[Tempo.Division.QUARTER.ordinal()];
        this.bar = click[Tempo.Division.WHOLE.ordinal()];

        lx.engine.tempo.addListener(this);
        lx.engine.tempo.tap.addListener(this::onTap, true);
        lx.engine.tempo.nudgeUp.addListener(this::onNudgeUp, true);
        lx.engine.tempo.nudgeDown.addListener(this::onNudgeDown, true);
        lx.engine.tempo.period.addListener(this::onPeriod, true);
        lx.engine.tempo.bpm.addListener(this::onBpm, true);
    }

    @Override
    public void run(double deltaMs, double enabledAmount) {
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
            LX.log("BASS HIT! High varying implied bpm: " + bpm);
        }

        if (bar.click()) {
//            LX.log("bar");
        } else if (beat.click()) {
//            LX.log("beat");
        }
    }
    public boolean click(Tempo.Division division) {
        return click[division.ordinal()].click();
    }

    public double basis(Tempo.Division division) {
        // todo: there's bad jumps when I use the clicks... modulator sync?
        return lx.engine.tempo.getBasis(division);
//         return click[division.ordinal()].getBasis();
    }

    private Click buildClick(Tempo.Division division) {
        Click click = new Click("Click_" + division.name(), period);
        click.tempoSync.setValue(true);
        click.tempoLock.setValue(true);
        click.tempoDivision.setValue(division);
        startModulator(click);
        return click;
    }

    private void refresh() {
        LX.log("DEBUG Audio refresh");
        updateFromPeriod();
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
        LX.log("Tempo BPM: " + this.bpm);
    }

    public void onPeriod(LXParameter period) {
        this.period = period.getValue();
        updateFromPeriod();
        LX.log("Tempo period (ms of 1 beat): " + this.period);
    }

    private void updateFromPeriod() {
        // Allow the beat detect to only trigger as fast as the tempo division
        // bassRetriggerMs =  15./16 * lx.engine.tempo.period.getValue() / tempoDivision.getObject().multiplier;
        teEngine.bassRetriggerMs = 15./16 * period / beat.tempoDivision.getObject().multiplier;

        // todo Make sure these phases don't auto reset, or that they need to or something
        Arrays.stream(click).forEach(click -> click.setPeriod(period));
    }

    // Any NA near beers brah?
    public void onTap(LXParameter tap) {

    }

    public void onNudgeUp(LXParameter nudgeUp) {

    }

    public void onNudgeDown(LXParameter nudgeDown) {

    }

    @Override
    protected void onEnable() {
        refresh();
        super.onEnable();
    }

    @Override
    protected void onDisable() {
        super.onDisable();
    }

    public static Audio get() {
        if (instance == null) throw new IllegalStateException("Ah fuck, static singleton Audio not ready. "
                + "Who would've ever thought this was a bad idea?");
        return instance;
    }
}
