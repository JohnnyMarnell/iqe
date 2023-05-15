package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.Tempo;

import java.util.concurrent.*;
import java.util.function.Consumer;
import java.util.stream.Stream;

/**
 * Here is where we can orchestrate actions, controls, and settings.
 * Uses OSC hooks, so we have easy, up-to-date info about the running project state,
 * plus ensures we can build easy clients.
 */
public class Orchestrator {
    private final OscBridge osc;
    private final LX lx;
    private static final ScheduledExecutorService executorService = Executors.newScheduledThreadPool(1);

    public Orchestrator(LX lx, OscBridge osc) {
        this.lx = lx;
        this.osc = osc;
        // haaaaax, the first OSC wiring dumps project state (super helpful), but don't want to fire events yet
         executorService.schedule(this::bindActions, 5, TimeUnit.SECONDS);
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
    }

    public void setParam(String component, String param, double value) {
        osc.command(path(component, param), value);
    }

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
