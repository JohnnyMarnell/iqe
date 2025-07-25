/**
 * Ported from the amazing PixelBlaze and Titanic's End work
 * https://github.com/titanicsend/LXStudio-TE
 * Thank you Ben H + Jeff V + Mark Slee!
 */

package titanicsend.pattern.pixelblaze;

import heronarts.lx.LX;
import heronarts.lx.model.LXPoint;
import heronarts.lx.parameter.BooleanParameter;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.parameter.LXParameterListener;
import titanicsend.pattern.TEPerformancePattern;

import javax.script.ScriptException;
import java.util.HashMap;

public abstract class PixelblazePattern extends TEPerformancePattern {
  public static final int RENDER_ERROR_LOG_INTERVAL_MS = 5_000;
  public Wrapper wrapper;
  long lastLogMs = 0; //to prevent spamming the logs with script errors
  public HashMap<String, LXParameter> patternParameters = new HashMap<>();

  // JKB note: these could be retired and replaced by views
  protected BooleanParameter enableEdges;
  protected BooleanParameter enablePanels;

  // JM: see hack notes here and glue
  protected BooleanParameter flipCoords;

  protected boolean clearNextFrame = false;

  /**
   * This should be overridden in subclasses to load a different source
   * file in the resources/pixelblaze directory. The '.js' extension is added.
   * @return
   */
  protected abstract String getScriptName();

  // Should this be done as onParameterChanged() instead?
  protected LXParameterListener modelPointsListener = lxParameter -> {
    if (wrapper != null) {
      try {
        this.clearNextFrame = true;
        wrapper.setPoints(getModelPoints());
      } catch (Exception e) {
        LX.error("Error updating points:" + e.getMessage());
      }
    }
  };

  public PixelblazePattern(LX lx) {
    super(lx, TEShaderView.ALL_POINTS);

    addCommonControls();

    enableEdges = new BooleanParameter("Edges", true);
    enablePanels = new BooleanParameter("Panels", true);
    flipCoords = new BooleanParameter("flipCoord", false);

//    enableEdges.addListener(modelPointsListener);
//    enablePanels.addListener(modelPointsListener);
    this.clearNextFrame = true;

    addParameter("enableEdges", enableEdges);
    addParameter("enablePanels", enablePanels);
    addParameter("flipCoord", flipCoords);

    try {
      wrapper = Wrapper.fromResource(getScriptName(), this, getModelPoints());
      wrapper.load();
    } catch (Exception e) {
      LX.error(e, "Error initializing Pixelblaze script");
    }
  }

  @Override
  public void dispose() {
//    enableEdges.removeListener(modelPointsListener);
//    enablePanels.removeListener(modelPointsListener);
    super.dispose();
  }

  public LXPoint[] getModelPoints() {
    return model.points.clone();

//    ArrayList<LXPoint> newPoints = new ArrayList<>(model.points.length);
//    if (enableEdges.getValueb()) {
//      newPoints.addAll(modelTE.edgePoints);
//    }
//    if (enablePanels.getValueb()) {
//      newPoints.addAll(modelTE.panelPoints);
//    }
//    return newPoints.toArray(new LXPoint[0]);
  }

  /**
   * Used by the glue to register discovered slider controls
   * @param key
   * @param label
   */
  public void addSlider(String key, String label) {
    if (parameters.containsKey(key)) {
      return;
    }
    LX.log("Pixelblaze adding parameter for " + label);
    CompoundParameter energy = new CompoundParameter(label, .5, 0, 1);
    addParameter(key, energy);
    patternParameters.put(key, energy);
  }

  /**
   * Used by the glue to invoke slider controls
   * @param key
   * @return
   */
  public double getSlider(String key) {
    LXParameter parameter = parameters.get(key);
    if (parameter != null) {
      return parameter.getValue();
    }
    return 0;
  }

  public void runTEAudioPattern(double deltaMs) {
    if (this.clearNextFrame) {
      this.clearNextFrame = false;
      clearPixels();
    }

    if (wrapper == null)
      return;

    try {
      wrapper.reloadIfNecessary();
      wrapper.render(deltaMs, colors);
    } catch (ScriptException | NoSuchMethodException sx) {
      //the show must go on, and we don't want to spam the logs.
      if (System.currentTimeMillis() - lastLogMs > RENDER_ERROR_LOG_INTERVAL_MS) {
        LX.log("Error rendering Pixelblaze script, " + wrapper.file + ":" + sx.getMessage());
        sx.printStackTrace();
        lastLogMs = System.currentTimeMillis();
      }
    } catch (Exception e) {
      e.printStackTrace();
//      LX.error(e); //NOTE: this will crash the pattern and make it unusable now
      return;
    }
  }

  public boolean getFlipCoords() {
    return flipCoords.getValueb();
  }
}