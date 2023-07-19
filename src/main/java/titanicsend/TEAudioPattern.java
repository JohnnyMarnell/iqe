/*
 * Taken from amazing Titanic's End repo!
 * https://github.com/titanicsend/LXStudio-TE
 */

package titanicsend;

import heronarts.lx.LX;
import heronarts.lx.audio.GraphicMeter;
import heronarts.lx.parameter.FunctionalParameter;
import heronarts.lx.parameter.LXParameter;
import org.iqe.AudioModulators;

import java.awt.*;

/**
 * PORTED: No longer to be used as redundant based class, the audio analysis
 * logic portions are used as part of audio engine of Audio.java class
 *
 *
 * Patterns should inherit from this if they wish to make use of live audio
 * data and several useful derived audio attributes, such as normalized
 * bass or treble levels.
 *
 * In the future we can implement gates, thresholds, or tempo inference.
 *
 * ToDo: Each pattern shouldn't have it's own copy of these audio things.
 * Need static members maintaining all audio computations.
 */
public class TEAudioPattern {
    // The GraphicMeter holds the analyzed frequency content for the audio input
    private final LX lx;
    public final GraphicMeter eq;

    // Fractions in 0..1 for the instantaneous frequency level this frame.
    // If we find this useful and track many more bands, a collection of ratio
    // tracker objects would make sense.
    public double volumeLevel;
    public double bassLevel;
    public double trebleLevel;

    // One of the demo patterns allows the VJ to vary how many bass bands
    // are tracked.
    protected int bassBandCount;

    // Accumulate recent frequency band measurements into an exponentially
    // weighted moving average.
    public TEMath.EMA avgVolume = new TEMath.EMA(0.5, .01);
    public TEMath.EMA avgBass = new TEMath.EMA(0.2, .01);
    public TEMath.EMA avgTreble = new TEMath.EMA(0.2, .01);

    /* Ratios of the instantaneous frequency levels in bands to their recent
     * running average. Using a ratio like this helps auto-scale to various
     * input levels. It would be best combined with a gate, so that long periods
     * of silence are ignored and return 0 instead of establishing a low bar.
     *
     * For example, with bassRatio:
     * .01 = 1% of recent average bass
     * 1    = Exactly the recent average bass
     * 5    = 5 times higher than the recent average bass
     *
     * Values depend greatly on the audio content, but 0.2 to 3 are common.
     */
    public double volumeRatio = .2;
    public double bassRatio = .2;
    public double trebleRatio = .2;

    // public double bassRetriggerMs;
    public LXParameter bassRetriggerMs;
    private double msSinceBassRise = 0;
    // Whether we suspect this frame represents a steep rise in bass level
    public boolean bassHit = false;

    public TEAudioPattern(LX lx) {
//        super(lx);
        this.lx = lx;

        this.eq = lx.engine.audio.meter;
        // goddamnit, this doesnt work
//        this.eq = new GraphicMeter("Meter", lx.engine.audio.input.mix, 32);
//        lx.engine.audio.addModulator(this.eq);


        bassBandCount = (int) Math.ceil(eq.numBands / 8.);
        // By default, 80% of a tempo-defined eighth note must have passed to bassHit
        // bassRetriggerMs = .8 * (lx.engine.tempo.period.getValue() / 2);
        bassRetriggerMs = new AudioModulators.FuncParam("bassRetriggerMs",
                () -> .8 * (lx.engine.tempo.period.getValue() / 2));
    }

//    @Override
//    protected void run(double deltaMs) {
//        computeAudio(deltaMs);
//        runTEAudioPattern(deltaMs);
//    }

    /** Call computeAudio() in a TEAudioPattern's run() once per frame to
     * update values that analyze and process the audio stream.
     *
     * @param deltaMs elapsed time since last frame, as provided in run(deltaMs)
     */
    public void computeAudio(double deltaMs) {
        // Instantaneous normalized (0..1) volume level
        volumeLevel = eq.getNormalizedf();

        /* Average bass level of the bottom `bassBands` frequency bands.
         * The default lx.engine.audio.meter breaks up sound into 16 bands,
         * so a `bassBandCount` of 2 averages the bottom 12.5% of frequencies.
         */
        bassLevel = eq.getAverage(0, bassBandCount);

        // Instantaneous average level of the top half of the frequency bins
        trebleLevel = eq.getAverage(eq.numBands / 2, eq.numBands / 2);

        /* Compute the ratio of the current instantaneous frequency levels to
         * their new, updated moving averages.
         */
        volumeRatio = volumeLevel / avgVolume.update(volumeLevel, deltaMs);
        bassRatio = bassLevel / avgBass.update(bassLevel, deltaMs);
        trebleRatio = trebleLevel / avgTreble.update(trebleLevel, deltaMs);

        bassHit = false;
        // If bass is over 20% higher than recent average
        // and greater than in the previous frame
        // and enough time has elapsed since we last triggered
        // mark the frame as a bassHit().
        if (bassLevel > 1.2 * avgBass.getValue()
                && bassLevel > lastBassLevel
                && msSinceBassRise > bassRetriggerMs.getValue()) {
            bassHit = true;
            msSinceBassRise = 0;
        }
        msSinceBassRise += deltaMs;
        lastBassLevel = bassLevel;
    }

    double lastBassLevel = 1;

    public double getBassLevel() {
        return bassLevel;
    }

    // Best attempt to detect beats and rising bass transients. Returns true if
    // we think this frame likely is directly following an audio beat.
    public boolean bassHit() {
        return bassHit;
    }

    // Call when a pattern knows it should be listening to bass
    // again even though a beat was just detected, such as a
    // "reset beat align" feature when listening for every 4th beat
    protected void resetBassGate() {
        msSinceBassRise = 0;
    }

    public double getTrebleLevel() {
        return trebleLevel;
    }

    public float getVolumeRatiof() {
        return (float) volumeRatio;
    }

    public double getBassRatio() {
        return bassRatio;
    }

    public double getTrebleRatio() {
        return trebleRatio;
    }

//    public void removeParameters(List<? extends LXParameter> parameters) {
//        for (LXParameter parameter : parameters) {
//            removeParameter(parameter);
//        }
//    }
//
//    public void addParameters(List<? extends LXParameter> newParameters) {
//        for(LXParameter parameter : newParameters) {
//            addParameter(parameter.getLabel(), parameter);
//        }
//    }
}
