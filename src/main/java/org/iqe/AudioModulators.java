package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.LXComponent;
import heronarts.lx.Tempo;
import heronarts.lx.modulator.*;
import heronarts.lx.parameter.MutableParameter;
import heronarts.lx.utils.LXUtils;

import java.util.Arrays;

/**
 * Work in Progress.
 *
 * The goal of this is to have easy project-wide modulators available in the UI, and non duplicated across
 * patterns and other components. They also tie into the Audio engine's computations, ones borrowed from Titanic's End
 * and ones we've created.
 *
 * I think there's minor hiccup with click jump, can see it in ZipStripPattern sometimes.
 * And, sadly, I can't figure out how to properly wire any of the click type modulation to work with our
 * "step" approach.
 * Also would like to add these automatically, but I don't know LX internals enough, especially the UI code parts.
 */
public class AudioModulators {
    private static LX lx;

    public static Boots boots;
    public static Quarter quarter;
    public static Bar bar;
    public static Half half;
    public static Eighth eighth;
    public static DottedEighth dottedEighth;
    public static Triplet triplet;

    public static VolumeLevel volumeLevel;
    public static BassLevel bassLevel;
    public static TrebleLevel trebleLevel;
    public static BassRatio bassRatio;
    public static TrebleRatio trebleRatio;

    public static VolumeAvg volumeAvg;
    public static BassAvg bassAvg;
    public static TrebleAvg trebleAvg;

    public static QuarterClick quarterClick;
    public static HalfClick halfClick;
    public static WholeClick wholeClick;

    public static BootsHit bootsHit;

    public static void initialize(LX lx) {
        AudioModulators.lx = lx;
        Arrays.stream(AudioModulators.class.getFields())
                .filter(field -> LXModulator.class.isAssignableFrom(field.getType()))
//                .peek(field -> LX.log("Audio modulator: " + field.getType().getSimpleName()))
                .forEach(field -> lx.registry.addModulator(field.getType().asSubclass(LXModulator.class)));
        lx.registry.addModulator(Root.class);
    }

    private static void register(LXComponent component) {
        Arrays.stream(AudioModulators.class.getFields())
                .filter(field -> field.getType().equals(component.getClass()))
                .forEach(field -> {
                    try {
                        if (field.get(AudioModulators.class) == null) {
                            LX.log("Binding Audio Modulator %s of type %s".formatted(field.getName(), field.getType().getSimpleName()));
                            field.set(AudioModulators.class, component);
                        } else {
                            LX.log("WARNING: multiple modulators for" + field.getType());
                        }
                    } catch (IllegalAccessException e) {
                        throw new RuntimeException(e);
                    }
            });
    }

    /** Tempo syncing is tricky, we want it centralized and uniform.
     *  The modulators probably come first, so adding this "Root" to tick the Audio engine */
    @LXCategory("Anal-yzed") @LXModulator.Global("Root") @LXModulator.Device("Root")
    public static class Root extends Gauge {
        @Override
        protected double computeValue(double deltaMs, double basis) {
            for (Audio.TempoClick click : Audio.get().clicks) {
                click.tick();
            }
            Audio.get().run(deltaMs);
            return super.computeValue(deltaMs, basis);
        }

        @Override
        double val() {
            return Audio.get().teEngine.volumeLevel;
        }
    }

    /** Meant to be a one shot pulse. Can have a shape to the LFO when it triggers */
    public static class Trigger extends VariableLFO {
        public Trigger() {
            label.setValue(getClass().getSimpleName(), true);
            setPeriod(AudioModulators.lx.engine.tempo.period);
            setPolarity(Polarity.UNIPOLAR);
            setLooping(false);
            register(this);
        }
    }

    /** Meant, I think, to be basis counters / uniform progress of beat ticks */
    public static class Beat extends VariableLFO {
        public Beat(Tempo.Division division) {
            label.setValue(getClass().getSimpleName() + "Beat", true);
            setLooping(true);
            tempoSync.setValue(true);
            tempoLock.setValue(true);
            tempoDivision.setValue(division);
            waveshape.setValue(LXWaveshape.UP);
            register(this);
        }
    }

    /** Similar to Java metrics, making an instantaneous value Gauge class
     *  Randomizer UI suffices (plus using the damping approach [final member unfortch]) */
    public abstract static class Gauge extends Randomizer {
        private final MutableParameter target = new MutableParameter(0.5);

        private final DampedParameter damper = (DampedParameter) new DampedParameter(this.target, this.speed, this.accel).start();

        public Gauge() {
            label.setValue(getClass().getSimpleName(), true);
            damping.setValue(false);
            looping.setValue(true);
            register(this);
        }

        @Override
        protected double computeValue(double deltaMs, double basis) {
            double val = val();
            if (loop() || finished()) {
                this.target.setValue(val());
            }
            this.damper.loop(deltaMs);
            return !damping.isOn() ? val : LXUtils.constrain(this.damper.getValue(), 0, 1);
        }

        abstract double val();
    }

    /** A one shot, non-periodic click modulator, e.g. a bass hit */
    public abstract static class Hit extends Gauge {
        abstract boolean isOn();

        @Override
        double val() {
            return isOn() ? 1.0 : 0.0;
        }
    }

    /** Clicks from tempo metronome, like the standard click modulator */
    public abstract static class Click extends Gauge {
        final private Tempo.Division division;

        public Click(Tempo.Division division) {
            this.division = division;
        }

        @Override
        double val() {
            return Audio.get().click(division) ? 1.0 : 0.0;
        }
    }

    @LXCategory("Rhythm") @LXModulator.Global("Boots") @LXModulator.Device("Boots")
    public static class Boots extends Trigger { }

    @LXCategory("Rhythm") @LXModulator.Global("BootsHit") @LXModulator.Device("BootsHit")
    public static class BootsHit extends Hit { public boolean isOn() { return Audio.get().bassHit(); } }

    @LXCategory("Rhythm") @LXModulator.Global("QuarterBeat") @LXModulator.Device("QuarterBeat")
    public static class Quarter extends Beat { public Quarter() { super(Tempo.Division.QUARTER); } }

    @LXCategory("Rhythm") @LXModulator.Global("BarBeat") @LXModulator.Device("BarBeat")
    public static class Bar extends Beat { public Bar() { super(Tempo.Division.WHOLE); } }

    @LXCategory("Rhythm") @LXModulator.Global("HalfBeat") @LXModulator.Device("HalfBeat")
    public static class Half extends Beat { public Half() { super(Tempo.Division.HALF); } }

    @LXCategory("Rhythm") @LXModulator.Global("EighthBeat") @LXModulator.Device("EighthBeat")
    public static class Eighth extends Beat { public Eighth() { super(Tempo.Division.EIGHTH); } }

    @LXCategory("Rhythm") @LXModulator.Global("DottedEighthBeat") @LXModulator.Device("DottedEighthBeat")
    public static class DottedEighth extends Beat { public DottedEighth() { super(Tempo.Division.EIGHTH_DOT); } }

    @LXCategory("Rhythm") @LXModulator.Global("TripletBeat") @LXModulator.Device("TripletBeat")
    public static class Triplet extends Beat { public Triplet() { super(Tempo.Division.QUARTER_TRIPLET); } }

    @LXCategory("Rhythm") @LXModulator.Global("QuarterClick") @LXModulator.Device("QuarterClick")
    public static class QuarterClick extends Click { public QuarterClick() { super(Tempo.Division.QUARTER_TRIPLET); } }
    @LXCategory("Rhythm") @LXModulator.Global("HalfClick") @LXModulator.Device("HalfClick")
    public static class HalfClick extends Click { public HalfClick() { super(Tempo.Division.HALF); } }
    @LXCategory("Rhythm") @LXModulator.Global("WholeClick") @LXModulator.Device("WholeClick")
    public static class WholeClick extends Click { public WholeClick() { super(Tempo.Division.WHOLE); } }

    @LXCategory("Anal-yzed") @LXModulator.Global("VolumeLevel") @LXModulator.Device("VolumeLevel")
    public static class VolumeLevel extends Gauge { double val() { return Audio.get().teEngine.volumeLevel; } }

    @LXCategory("Anal-yzed") @LXModulator.Global("BassLevel") @LXModulator.Device("BassLevel")
    public static class BassLevel extends Gauge { double val() { return Audio.get().teEngine.bassLevel; } }

    @LXCategory("Anal-yzed") @LXModulator.Global("TrebleLevel") @LXModulator.Device("TrebleLevel")
    public static class TrebleLevel extends Gauge { double val() { return Audio.get().teEngine.trebleLevel; } }

    @LXCategory("Anal-yzed") @LXModulator.Global("BassRatio") @LXModulator.Device("BassRatio")
    public static class BassRatio extends Gauge { double val() { return Audio.get().teEngine.bassRatio; } }

    @LXCategory("Anal-yzed") @LXModulator.Global("TrebleRatio") @LXModulator.Device("TrebleRatio")
    public static class TrebleRatio extends Gauge { double val() { return Audio.get().teEngine.trebleRatio; } }

    @LXCategory("Anal-yzed") @LXModulator.Global("VolumeAvg") @LXModulator.Device("VolumeAvg")
    public static class VolumeAvg extends Gauge { double val() { return Audio.get().teEngine.avgVolume.getValue(); } }
    @LXCategory("Anal-yzed") @LXModulator.Global("BassAvg") @LXModulator.Device("BassAvg")
    public static class BassAvg extends Gauge { double val() { return Audio.get().teEngine.avgBass.getValue(); } }

    @LXCategory("Anal-yzed") @LXModulator.Global("TrebleAvg") @LXModulator.Device("TrebleAvg")
    public static class TrebleAvg extends Gauge { double val() { return Audio.get().teEngine.avgTreble.getValue(); } }
}
