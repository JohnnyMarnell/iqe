package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.LXComponent;
import heronarts.lx.Tempo;
import heronarts.lx.modulator.*;
import heronarts.lx.parameter.*;
import heronarts.lx.utils.LXUtils;

import java.lang.reflect.Field;
import java.util.Arrays;
import java.util.List;
import java.util.function.Consumer;
import java.util.function.Supplier;

import static org.iqe.GlobalControls.BASS;
import static org.iqe.GlobalControls.TEMPO;
import static org.iqe.LXPluginIQE.INTERNAL;
import static org.iqe.Audio.GlobalParams;

/**
 * The goal of this is to have easy project-wide modulators available in the UI, and non duplicated across
 * patterns and other components. They also tie into the Audio engine's computations, ones borrowed from Titanic's End
 * and ones we've created.
 * They're re-using some UI from LX, rather than have to figure that out.
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

    public static GlobalControls controls;

    public static Root rootModulator;
    public static GlobalParams globalParams;

    public static void initialize(LX lx) {
        AudioModulators.lx = lx;
        addFieldsToLXRegistry(LXModulator.class, lx.registry::addModulator);
        lx.registry.addEffect(GlobalControls.class);
        lx.registry.addEffect(Audio.NO_TOUCHY.class);
        lx.engine.addLoopTask(deltaMs -> Audio.get().engineLoop(deltaMs));
    }

    public static void register(LXComponent component) {
        List<Field> fields = Arrays.stream(AudioModulators.class.getFields())
                .filter(field -> field.getType().equals(component.getClass())).toList();
        if (fields.size() == 1) bind(component, fields.get(0));
        else {
            fields = Arrays.stream(AudioModulators.class.getFields())
                    .filter(field -> field.getType().isAssignableFrom(component.getClass())).toList();
            if (fields.size() != 1) throw new IllegalStateException("None of this was worth it");
            bind(component, fields.get(0));
        }
    }

    private static void bind(LXComponent component, Field field) {
        try {
            if (field.get(AudioModulators.class) == null) {
                LX.log("Binding Audio Component %s of type %s".formatted(field.getName(), field.getType().getSimpleName()));
                field.set(AudioModulators.class, component);
            } else {
                throw new IllegalStateException("There should only be one, but multiple components for " + field.getType());
            }
        } catch (IllegalAccessException e) {
            throw new RuntimeException(e);
        }
    }

    private static <T> void addFieldsToLXRegistry(Class<T> clazz, Consumer<Class<T>> adder) {
        Arrays.stream(AudioModulators.class.getFields())
                .filter(field -> clazz.isAssignableFrom(field.getType()))
                .forEach(field -> adder.accept((Class<T>) field.getType()));
    }

    /** Tempo syncing is tricky, we want it centralized and uniform.
     *  The modulators seem to come first, so adding this "Root" to tick the Audio engine,
     *  main entry point for us */
    @LXCategory(INTERNAL) @LXModulator.Global(INTERNAL) @LXModulator.Device(INTERNAL) @LXComponent.Hidden
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

    /** I want to be able to use lambdurz */
    public static class FuncParam extends FunctionalParameter {
        private Supplier<Double> calc;

        public FuncParam(String label, Supplier<Double> calc) {
            super(label);
            this.calc = calc;
        }

        @Override
        public double getValue() {
            return calc.get();
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
            return this.chance.getValue() / 100. * Audio.periodOf(Tempo.Division.EIGHT);
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

    /**
     * There is a default / global click setting (Patterns and components can override, optionally),
     * so this modulator modulates whatever that setting is courrently.
     */
    // todo: Make it actually delegate to the other Trigger instances
    @LXCategory("Rhythm") @LXModulator.Global("GlobalClick") @LXModulator.Device("GlobalClick")
    public static class GlobalClick extends Trigger {

        @Override
        protected boolean shouldTrigger(double val) {
            LOG.debug("Global click tick");
            boolean triggering = false;
            int option = GlobalControls.defaultClick.getValuei();
            if (option == BASS) {
                triggering = bootsClick.shouldTrigger(val);
            } else if (option >= TEMPO) {
                triggering = Audio.get().click(Tempo.Division.values()[option - TEMPO]);
            }
            return triggering;
        }

        @Override
        protected double val() {
            double val = 0.0;
            int option = GlobalControls.defaultClick.getValuei();
            if (option == BASS) {
                val = bootsClick.val();
            } else if (option >= TEMPO) {
                val = Audio.get().basis(Tempo.Division.values()[option - TEMPO]);
            }
            return val;
        }
    }

    /**
     * A "hit" is not sync-locked to tempo, it is triggered and ramps for some duration
     * (usually one beat / quarter note), and can limit re-triggering. So far BootsClick is
     * a modulator for bass "hit".
     */
    // todo: hooboy... this and basically anything else that does tempo / period math needs to obviously
    //    be updated with tempo changes (so, a wire listener)
    @LXCategory("Rhythm") @LXModulator.Global("BootsClick") @LXModulator.Device("BootsClick")
    public static class BootsClick extends Trigger {
        public BootsClick() {
            setPeriodFrom(Tempo.Division.QUARTER);
        }

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
