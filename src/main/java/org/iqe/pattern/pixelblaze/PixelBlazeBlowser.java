package org.iqe.pattern.pixelblaze;

import com.google.gson.JsonObject;
import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.parameter.*;
import org.iqe.LOG;
import titanicsend.pattern.pixelblaze.Wrapper;

import java.io.File;
import java.util.Collection;
import java.util.List;

@LXCategory("PixelBlaze")
public class PixelBlazeBlowser extends PixelblazeHelper {

    public final DiscreteParameter script;

    public final CompoundParameter speed = new CompoundParameter("timeShift", 1.0, 0.001, 1.0);
    public final CompoundParameter timeDelta = new CompoundParameter("timeDelta", 0.0, -1., 1.);
    public final CompoundParameter timeDeltaMax = new CompoundParameter("timeDMax", 0.0, 0., 1.5);

    public final StringParameter scriptName = new StringParameter("Script Name", "test.js")
            .setDescription("Path to the Pixelblaze script");

    public final BooleanParameter reset =
            new BooleanParameter("Reset", false)
                    .setMode(BooleanParameter.Mode.MOMENTARY)
                    .setDescription("Resets the Pixelblaze JS engine for this script");

    public final MutableParameter onReload = new MutableParameter("Reload");
    public final StringParameter error = new StringParameter("Error", "");
    protected final LXParameterListener scriptListener;

    protected JsonObject json = null;
    protected double elapsedMs = 0.0d;

    public PixelBlazeBlowser(LX lx) {
        super(lx);
        script = new DiscreteParameter("script", PixelblazePatterns.patternData.keySet().toArray(new String[0]));
        addParameter("script", script);
        addParameter("speed", speed);
        addParameter("timeDelta", timeDelta);
        addParameter("timeDMax", timeDeltaMax);

        removeParameter("enablePanels");
        addParameter("scriptName", scriptName);
        addParameter("reload", onReload);
        addParameter("error", error);
        this.scriptListener = p -> this.setScript();
        script.addListener(scriptListener, true);
        onReload.bang();
    }

    @Override
    public void dispose() {
        script.removeListener(scriptListener);
    }

    @Override
    protected String getScriptName() {
        return "__pbb_" + (script == null ? PixelblazePatterns.patternData.keySet().iterator().next() : script.getOption());
    }

    public Collection<CompoundParameter> getSliders() {
        return patternParameters.values().stream().map(p -> (CompoundParameter) p).toList();
    }


    public void setScript() {
        String path = "resources/pixelblaze/" + getScriptName() + ".js";
        File placeholder = new File(path);
        if (wrapper == null) {
            wrapper = new Wrapper(placeholder, this, getModelPoints());
        } else {
            // When pattern JS is loaded via glue.js + Wrapper.load(), it will add parameters dynamically,
            // make sure we first remove any previously loaded
            List<String> paths = getParameters().stream()
                    .peek(p -> LOG.info("Param present path {}, label {}", p.getPath(), p.getLabel()))
                    .filter(p -> p.getPath().startsWith("slider"))
                    .map(LXParameter::getPath).toList();
            LOG.info("Removing pixelblaze parameters {}", paths);
            paths.forEach(this::removeParameter);
            paths.forEach(p -> patternParameters.remove(p));
            wrapper.file = PixelblazePatterns.standardResource(placeholder);
            wrapper.lastModified = -1;
        }
    }

    @Override
    public void load(LX lx, JsonObject obj) {
        super.load(lx, obj);
        this.json = obj.deepCopy();
    }

    @Override
    public void save(LX lx, JsonObject obj) {
        super.save(lx, obj);
        this.json = obj.deepCopy();
    }

    @Override
    public void addSlider(String key, String label) {
        super.addSlider(key, label);

        // after this slider is added, set its initial value to whatever was saved last in this pattern def,
        // if available
        if (this.json != null && this.json.has("parameters")) {
            ((JsonObject) this.json.get("parameters"))
                    .entrySet().stream()
                    .filter(e -> e.getKey().equals(key))
                    .map(e -> e.getValue().getAsDouble())
                    .forEach(val -> getParameter(key).setValue(val));
        }
    }

    /** Apply stretch / shrink to the elapsed delta change of milliseconds, plus keep the running clock */
    @Override
    protected void run(double deltaMs) {
        deltaMs = deltaMs * this.speed.getValue();
        deltaMs = deltaMs + this.timeDelta.getValue() * this.timeDeltaMax.getValue();

        if (elapsedMs == 0) elapsedMs = lx.engine.nowMillis;
        elapsedMs = elapsedMs + deltaMs;
        super.run(deltaMs);
    }

    @Override
    public double getTime() {
        return elapsedMs;
    }

    /** TE code had a separate approach for "getTime" vs "getTimeMs", but I'm keeping them
     *  the same, hopefully it won't matter. */
    @Override
    public long getTimeMs() {
        return (long) elapsedMs;
    }
}
