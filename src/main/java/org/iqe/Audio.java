package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.Tempo;
import heronarts.lx.effect.LXEffect;
import heronarts.lx.modulator.Click;
import heronarts.lx.parameter.LXParameter;

import java.util.Arrays;

// todo: decide on Singleton-ify
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

    public boolean click(Tempo.Division division) {
        return click[division.ordinal()].click();
    }

    private Click buildClick(Tempo.Division division) {
        Click click = new Click("Click_" + division.name(), period);
        click.tempoSync.setValue(true);
        click.tempoDivision.setValue(division);
        startModulator(click);
        return click;
    }

    private void refresh() {
        LX.log("DEBUG Audio refresh");
        updateFromPeriod();
    }

    @Override
    public void run(double deltaMs, double enabledAmount) {
        long now = System.currentTimeMillis();
        teEngine.computeAudio(deltaMs);
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
