/**
 * Ported from the amazing PixelBlaze and Titanic's End work
 * https://github.com/titanicsend/LXStudio-TE
 * Thank you Ben H + Jeff V + Mark Slee!
 */

package titanicsend.pattern.pixelblaze;

import javax.script.*;
import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;

import heronarts.lx.LX;
import heronarts.lx.model.LXPoint;
import org.iqe.pattern.pixelblaze.PixelblazePatterns;
import org.openjdk.nashorn.api.scripting.JSObject;
import org.openjdk.nashorn.api.scripting.NashornScriptEngineFactory;
import titanicsend.pattern.PortFacade_TEPerformancePattern;

public class Wrapper {

  //NOTE these are thread-safe, if used with separate bindings
  //https://stackoverflow.com/a/30159424/910094
  public static final ScriptEngine engine;
  public static final Compilable compilingEngine;
  public static HashMap<Path, CachedScript> scripts = new HashMap<>();
  static {
    NashornScriptEngineFactory factory = new NashornScriptEngineFactory();
    engine = factory.getScriptEngine("--language=es6");
    compilingEngine = (Compilable) engine;
  }

  public static class CachedScript {
    CompiledScript compiledScript;
    long lastModified;
    public CachedScript(CompiledScript compiledScript, long lastModified) {
      this.compiledScript = compiledScript;
      this.lastModified = lastModified;
    }
  }

  public static synchronized CompiledScript compile(Path path) throws ScriptException, IOException {
    CachedScript cachedScript = scripts.get(path);
    File file = path.toFile();
    // Johnny Marnell port: see method
    file = org.iqe.pattern.pixelblaze.PixelblazePatterns.standardResource(path);
    if (cachedScript == null || cachedScript.lastModified != file.lastModified()) {
      String js = Files.readString(file.toPath());
      long lastModified = file.lastModified();
      js = js.replaceAll("\\bexport\\b", "");
      CompiledScript compiled = compilingEngine.compile(js);

      cachedScript = new CachedScript(compiled, lastModified);
      scripts.put(path, cachedScript);
    }

    return cachedScript.compiledScript;
  }

  public static Wrapper fromResource(String pbClass, PortFacade_TEPerformancePattern pattern, LXPoint[] points) throws Exception {
    // Johnny Marnell port: see method
    if (pattern instanceof org.iqe.pattern.pixelblaze.PixelblazePatterns.PixelBlazeBlowser)
      return org.iqe.pattern.pixelblaze.PixelblazePatterns.wrapper(pbClass, pattern, points);
    if (pattern instanceof org.iqe.pattern.pixelblaze.PixelblazePatterns.PBP) pbClass
            = ((org.iqe.pattern.pixelblaze.PixelblazePatterns.PBP) pattern).getScriptName();
    File file = org.iqe.pattern.pixelblaze.PixelblazePatterns.standardResource(Path.of("resources/pixelblaze/" + pbClass + ".js"));
    return new Wrapper(file, pattern, points);
  }

  File file;
  PortFacade_TEPerformancePattern pattern;
  LXPoint[] points;
  long lastModified;
  Bindings bindings = engine.createBindings();
  String renderName;
  boolean hasError = false;

  public Wrapper(File file, PortFacade_TEPerformancePattern pattern, LXPoint[] points) throws ScriptException, IOException {
    this.file = file;
    this.pattern = pattern;
    this.points = points;
  }

  public void reloadIfNecessary() throws ScriptException, IOException, NoSuchMethodException {
    if (file.lastModified() != lastModified) {
      LX.log("Reloading pattern: " + file.getName());
      load();
    }
  }

  public void load() throws IOException, ScriptException, NoSuchMethodException {
    try {

      bindings = engine.createBindings();

      // Johnny Marnell port: see method
//      CompiledScript glueScript = compile(Path.of("resources/pixelblaze/glue.js"));
      CompiledScript glueScript = compile(
              org.iqe.pattern.pixelblaze.PixelblazePatterns.standardResource(Path.of("resources/pixelblaze/glue.js")).toPath());

      CompiledScript patternScript = compile(file.toPath());
      lastModified = file.lastModified();

      bindings.put("pixelCount", points.length);
      bindings.put("__pattern", pattern);
      bindings.put("__now", pattern.getTimeMs());

      glueScript.eval(bindings);
      patternScript.eval(bindings);
      ((JSObject)bindings.get("glueRegisterControls")).call(null);

      LX.log("Pattern loaded, ready:" + file.getName());

      hasError = false;
    } catch (Throwable t) {
      hasError = true;
      throw t;
    }
  }

  public void render(double deltaMs, int[] colors) throws ScriptException, NoSuchMethodException {
    if (hasError)
      return;
    bindings.put("__now", pattern.getTimeMs());
    bindings.put("__points", points);
    bindings.put("__colors", colors);

    JSObject glueBeforeRender = (JSObject) bindings.get("glueBeforeRender");
    if (glueBeforeRender != null)
      glueBeforeRender.call(null, deltaMs, pattern.getTimeMs(), points, colors);
    JSObject glueRender = (JSObject) bindings.get("glueRender");
    if (glueRender != null)
      glueRender.call(null);

  }

  /**
   * Updates the points that the pattern will operate on, reloading if necessary.
   * @param points
   * @throws ScriptException
   * @throws IOException
   * @throws NoSuchMethodException
   */
  public void setPoints(LXPoint[] points) throws ScriptException, IOException, NoSuchMethodException {
    if (this.points == points)
      return;
    this.points = points;
    load();
  }

}
