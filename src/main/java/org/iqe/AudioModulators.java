package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.LXComponent;
import heronarts.lx.Tempo;
import heronarts.lx.effect.LXEffect;
import heronarts.lx.modulator.*;
import heronarts.lx.parameter.*;
import heronarts.lx.utils.LXUtils;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import static org.iqe.AudioModulators.Controls.BASS;
import static org.iqe.AudioModulators.Controls.TEMPO;

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

    public static VolumeLevel volumeLevel;
    public static BassLevel bassLevel;
    public static TrebleLevel trebleLevel;
    public static BassRatio bassRatio;
    public static TrebleRatio trebleRatio;

    public static VolumeAvg volumeAvg;
    public static BassAvg bassAvg;
    public static TrebleAvg trebleAvg;

    public static GlobalClick globalClick;
    public static EighthClick eighthClick;
    public static DottedEighthClick dottedEighthClick;
    public static QuarterClick quarterClick;
    public static HalfClick halfClick;
    public static BarClick barClick;

    public static BootsClick bootsClick;

    public static Controls controls;

    public static void initialize(LX lx) {
        AudioModulators.lx = lx;
        Arrays.stream(AudioModulators.class.getFields())
                .filter(field -> LXModulator.class.isAssignableFrom(field.getType()))
                .forEach(field -> lx.registry.addModulator(field.getType().asSubclass(LXModulator.class)));
        lx.registry.addModulator(Root.class);
        lx.registry.addEffect(Controls.class);
        lx.engine.addLoopTask(deltaMs -> Audio.get().engineLoop(deltaMs));
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
     *  The modulators seem to come first, so adding this "Root" to tick the Audio engine,
     *  main entry point for us */
    @LXCategory("NO_TOUCHY") @LXModulator.Global("NO_TOUCHY") @LXModulator.Device("Root")
    public static class Root extends Trigger {
        @Override
        protected double computeValue(double deltaMs, double basis) {
            LOG.debug("Root Modulator tick");
            Audio.get().run(deltaMs);
            return super.computeValue(deltaMs, basis);
        }

        @Override
        protected double val() {
            return Audio.get().teEngine.volumeLevel;
        }
    }

    /** A lot of the finagling and hacky stuff here is because I don't yet know about proper UI
     *  and organization. Adding a global effect that I can throw controls into */
    // todo: move to its own class, start leveraging OSC and adding actions with trigger buttons
    //      like, 8 bar ramp up sparkles, quick off sparkles (or any other kind of dynamics)
    // todo: random to-do, add to audio engine (and modulators? tho not sure I could "script" what I want thru UI)
    //     a bass drop out and re-enter by counting hits
    public static class Controls extends LXEffect {
        public static final List<String> clicks = buildClicks();
        public static final DiscreteParameter defaultClick =
                new DiscreteParameter("syncMode", clicks.toArray(new String[0]))
                        .setDescription("Tempo division (quantize) amount or triggering (e.g. from bass) that default / global setting uses.");
        public static final BooleanParameter bassDynamics = new BooleanParameter("bassDynamics")
                .setDescription("Whether or not overall mood / energy can respond to bass pattern changes (e.g. drop)")
                .setValue(true);

        public static final TriggerParameter build = new TriggerParameter("build")
                .setDescription("Trigger a build up dynamic event");
        public static final TriggerParameter highIntensity = new TriggerParameter("highIntensity")
                .setDescription("Trigger a high intensity dynamic event");

        public static final int BASS = 0;
        public static final int TEMPO = 1;
        public Controls(LX lx) {
            super(lx);
            this.label.setValue("Global Controls");
            this.setDescription("Global / default control panel");
            this.addParameter("defaultSyncMode", defaultClick);
            this.addParameter("bassDynamics", bassDynamics);
            this.addParameter("build", build);
            this.addParameter("highIntensity", highIntensity);

            defaultClick.setValue(clicks.indexOf(Tempo.Division.QUARTER.toString()), true);

            register(this);
        }

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

    /**
     * This modulator is mappable / provides automation as both trigger event and parameter output (the latter
     * same as basis ramp, e.g. 0 -> 1 over duration of beat).
     *
     * Jerry rigging Randomizer UI since it has trigger + modulator outs, plus re-using some controls
     * (yet more final problems, unfortch).
     */
    public abstract static class Trigger extends Randomizer {
        private long lastTrigger;
        protected boolean limitRetrigger = false;
        private final MutableParameter target = new MutableParameter(0.0);
        private final DampedParameter damper = (DampedParameter)
                new DampedParameter(this.target, this.speed, this.accel).start();


        public Trigger() {
            label.setValue(getClass().getSimpleName(), true);
            damping.setValue(false);
            looping.setValue(true);
            max.setDescription("Maximum value of range to trigger on").setValue(1.0);
            min.setDescription("Minimum value of range to trigger on").setValue(0.5);
            chance.setDescription("Percent of 8 bars time to allow re-trigger / duration");
            setPeriodFrom(Tempo.Division.QUARTER); // default assume quarter note duration
            register(this);
        }

        @Override
        protected double computeValue(double deltaMs, double basis) {
            double val = val();
            boolean triggering = willTrigger(val);
            this.getTriggerSource().setValue(triggering);

            this.target.setValue(val());
            this.damper.loop(deltaMs);
            return !damping.isOn() ? val : LXUtils.constrain(this.damper.getValue(), 0, 1);
        }

        public void setPeriodFrom(Tempo.Division division) {
            this.chance.setValue(Tempo.Division.EIGHT.multiplier / division.multiplier * 100.);
        }

        protected double period() {
            return this.chance.getValue() / 100. * Audio.periodOf(Tempo.Division.WHOLE);
        }

        protected double elapsedBasis() {
            return (Audio.now() - lastTrigger) / period();
        }

        private boolean willTrigger(double val) {
            boolean triggering = (!limitRetrigger || elapsedBasis() >= 1.0) && shouldTrigger(val);
            if (triggering) {
                lastTrigger = Audio.now();
            }
            return triggering;
        }

        protected boolean shouldTrigger(double val) {
            return false;
        }
        protected double val() {
            return 0.0;
        };
    }


    /**
     * Easy click / tempo sync+lock aligned based triggers, per some division
     */
    public static class TempoTrigger extends Trigger {
        final private Tempo.Division division;
        public TempoTrigger(Tempo.Division division) {
            this.division = division;
            setPeriodFrom(division);
        }

        @Override
        protected boolean shouldTrigger(double val) {
            return Audio.get().click(division);
        }

        @Override
        protected double val() {
            return Audio.get().basis(division);
        }
    }
    @LXCategory("Rhythm") @LXModulator.Global("GlobalClick") @LXModulator.Device("GlobalClick")
    public static class GlobalClick extends Trigger {

        @Override
        protected boolean shouldTrigger(double val) {
            LOG.debug("Global click tick");
            boolean triggering = false;
            int option = Controls.defaultClick.getValuei();
            if (option == BASS) {
                triggering = bootsClick.shouldTrigger(val);
            } else if (option >= TEMPO) {
                // todo: use global modulator, even though would be same
                triggering = Audio.get().click(Tempo.Division.values()[option - TEMPO]);
            }
            return triggering;
        }

        @Override
        protected double val() {
            double val = 0.0;
            int option = Controls.defaultClick.getValuei();
            if (option == BASS) {
                val = bootsClick.val();
            } else if (option >= TEMPO) {
                // todo: use global modulator, even though would be same
                val = Audio.get().basis(Tempo.Division.values()[option - TEMPO]);
            }
            return val;
        }
    }

    /**
     * A hit is not sync-locked to tempo, it is triggered and ramps for some duration
     * (usually one beat / quarter note), and can limit re-triggering
     */


    @LXCategory("Rhythm") @LXModulator.Global("BootsClick") @LXModulator.Device("BootsClick")
    public static class BootsClick extends Trigger {
        @Override
        protected boolean shouldTrigger(double val) {
            return Audio.get().bassHit();
        }

        @Override
        protected double val() {
            double basis = elapsedBasis();
            return basis <= 1.0 ? basis : 0.0;
        }
    }

    /***
     * Tempo clicks
     */
    @LXCategory("Rhythm") @LXModulator.Global("EighthClick") @LXModulator.Device("EighthClick")
    public static class EighthClick extends TempoTrigger { public EighthClick() { super(Tempo.Division.EIGHTH); } }
    @LXCategory("Rhythm") @LXModulator.Global("DottedEighthClick") @LXModulator.Device("DottedEighthClick")
    public static class DottedEighthClick extends TempoTrigger { public DottedEighthClick() { super(Tempo.Division.EIGHTH_DOT); } }
    @LXCategory("Rhythm") @LXModulator.Global("QuarterClick") @LXModulator.Device("QuarterClick")
    public static class QuarterClick extends TempoTrigger { public QuarterClick() { super(Tempo.Division.QUARTER); } }
    @LXCategory("Rhythm") @LXModulator.Global("HalfClick") @LXModulator.Device("HalfClick")
    public static class HalfClick extends TempoTrigger { public HalfClick() { super(Tempo.Division.HALF); } }
    @LXCategory("Rhythm") @LXModulator.Global("BarClick") @LXModulator.Device("BarClick")
    public static class BarClick extends TempoTrigger { public BarClick() { super(Tempo.Division.WHOLE); } }

    /****
     * Volume Levels, Anal-yzed
     */
    @LXCategory("Anal-yzed") @LXModulator.Global("VolumeLevel") @LXModulator.Device("VolumeLevel")
    public static class VolumeLevel extends Trigger { protected double val() { return Audio.get().teEngine.volumeLevel; } }

    @LXCategory("Anal-yzed") @LXModulator.Global("BassLevel") @LXModulator.Device("BassLevel")
    public static class BassLevel extends Trigger { protected double val() { return Audio.get().teEngine.bassLevel; } }

    @LXCategory("Anal-yzed") @LXModulator.Global("TrebleLevel") @LXModulator.Device("TrebleLevel")
    public static class TrebleLevel extends Trigger { protected double val() { return Audio.get().teEngine.trebleLevel; } }

    @LXCategory("Anal-yzed") @LXModulator.Global("BassRatio") @LXModulator.Device("BassRatio")
    public static class BassRatio extends Trigger { protected double val() { return Audio.get().teEngine.bassRatio; } }

    @LXCategory("Anal-yzed") @LXModulator.Global("TrebleRatio") @LXModulator.Device("TrebleRatio")
    public static class TrebleRatio extends Trigger { protected double val() { return Audio.get().teEngine.trebleRatio; } }

    @LXCategory("Anal-yzed") @LXModulator.Global("VolumeAvg") @LXModulator.Device("VolumeAvg")
    public static class VolumeAvg extends Trigger { protected double val() { return Audio.get().teEngine.avgVolume.getValue(); } }
    @LXCategory("Anal-yzed") @LXModulator.Global("BassAvg") @LXModulator.Device("BassAvg")
    public static class BassAvg extends Trigger { protected double val() { return Audio.get().teEngine.avgBass.getValue(); } }

    @LXCategory("Anal-yzed") @LXModulator.Global("TrebleAvg") @LXModulator.Device("TrebleAvg")
    public static class TrebleAvg extends Trigger { protected double val() { return Audio.get().teEngine.avgTreble.getValue(); } }
}
