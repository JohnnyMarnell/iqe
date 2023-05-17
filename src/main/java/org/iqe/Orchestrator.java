package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.Tempo;

import java.util.concurrent.*;
import java.util.function.Consumer;
import java.util.stream.Stream;

import static org.iqe.Audio.bars;

/**
 * Here is where we can orchestrate actions, controls, and settings.
 * Uses OSC hooks, so we have easy, up-to-date info about the running project state,
 * plus ensures we can build easy clients.
 */
public class Orchestrator {
    private final OscBridge osc;
    private final LX lx;
    public static final ScheduledExecutorService executorService = Executors.newScheduledThreadPool(4);

    public Orchestrator(LX lx, OscBridge osc) {
        this.lx = lx;
        this.osc = osc;
        bindActions();
    }

    // todo: Need exclusivity
    // todo: LFO ramp control
    // todo: optimize
    public void bindActions() {
        LOG.info("Binding Orchestrator OSC actions");

        osc.on("/lx/mixer/master/effect/1/build", e -> rampParameter("Sparkle", "amount",
                Audio.periodOf(Tempo.Division.EIGHT)));
        osc.on("/lx/mixer/master/effect/1/highIntensity", e -> rampParameterDown("Sparkle", "amount",
                Audio.periodOf(Tempo.Division.HALF)));

        osc.on("/lx/mixer/master/effect/1/pFire", e -> setParam("PillarFire", "syncTrigger", e.getFloat()));
        osc.on("/lx/mixer/master/effect/1/bassBnc", e -> setParam("Hue + Saturation", "enabled", e.getFloat()));
        osc.onTrigger("/lx/mixer/master/effect/1/color", e -> osc.command("/lx/palette/triggerSwatchCycle"));
        osc.onTrigger("/lx/mixer/master/effect/1/pattern", e -> osc.command("/lx/mixer/channel/1/triggerPatternCycle"));
        osc.onTrigger("/lx/mixer/master/effect/1/freeBass", e -> freeBass());

    }

    public void setParam(String component, String param, double value) {
        osc.command(path(component, param), value);
    }

    // todo: again need exclusivity, and time extension behavior?
    /* For some period of time, allow the bass hit detects to re-trigger fastur hardur strongur */
    public void freeBass() {
        Audio.get().limitBassRetrigger.setValue(false);
        schedule(() -> Audio.get().limitBassRetrigger.setValue(true), bars(2));
    }

    public static void schedule(Runnable task, double millis) {
        executorService.schedule(task, (long) millis, TimeUnit.MILLISECONDS);
    }

    // todo: use LFO (modulator added somewhere and removed when done?)
    public void ramp(Consumer<Double> action, double periodMillis) {
        Audio.get().addStartTask(new RampingLoopTask(action, periodMillis));
    }

    public void rampParameter(String component, String param, double periodMillis) {
        ramp(v -> setParam(component, param, v), periodMillis);
    }

    public void rampParameterDown(String component, String param, double periodMillis) {
        ramp(v -> setParam(component, param, 1. - v), periodMillis);
    }

    public class RampingLoopTask implements Audio.Task {
        private final Consumer<Double> action;
        private Long startMillis;
        private double periodMs;

        public RampingLoopTask(Consumer<Double> action, double periodMs) {
            this.action = action;
            this.periodMs = periodMs;
        }

        @Override
        public void run(double deltaMs) {
            if (startMillis == null) startMillis = lx.engine.nowMillis;
            double basis = (lx.engine.nowMillis - startMillis) / periodMs;
            action.accept(Math.min(basis, 1.));
            if (basis >= 1.) Audio.get().removeStartTask(this);
        }
    }

    // todo: cache, make fast
    public String path(String componentLabel) {
        return paths(componentLabel).findAny().orElseThrow();
    }

    public String path(String componentLabel, String parameter) {
        return path(componentLabel) + "/" + parameter;
    }

    public Stream<String> paths(String componentLabel) {
        return osc.state.entrySet().stream()
                .filter(e -> e.getKey().endsWith("/label"))
                .filter(e -> e.getValue().size() >= 1)
                .filter(e -> e.getValue().get(0).toString().equals(componentLabel))
                .map(e -> e.getKey().substring(0, e.getKey().length() - 6));
    }
}
