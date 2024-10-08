package org.iqe.pattern.pixelblaze;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.pattern.LXPattern;
import org.iqe.Audio;
import org.openjdk.nashorn.api.tree.Tree;
import titanicsend.pattern.pixelblaze.Wrapper;

import javax.script.Bindings;
import javax.script.CompiledScript;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.URI;
import java.net.URISyntaxException;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.nio.file.attribute.BasicFileAttributes;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.TreeMap;
import java.util.stream.StreamSupport;
import java.util.zip.GZIPInputStream;

/**
 * This used to be more of a junk drawer, maybe it's a little better now.
 * Mainly (IIRC), static methods that I might call elsewhere while porting
 * (e.g. in "Wrapper", to find / resolve PixelBlaze JavaScript source files)
 *
 * I'm all inheritance / .class'd out y'all...
 */

public class PixelblazePatterns {
    public static CompiledScript extraGlueScript = null;
    private static final Gson gson = new Gson();
    public static final Map<String, String> patternData = loadPatternData();

    /** Johnny Marnell port:
     * Much of the Pixelblaze code is File class heavy
     * Proper java structure package uses src/main/resources directory, removing redundant + breaking prepend
     * Make work for all translations, running local FS or jar */
    public static File standardResource(Path path) {
        Path resourcePath = Path.of(
                path.toAbsolutePath().toString()
                        .replaceAll("^.*/resources/", "")
                        .replaceAll("^.*classes/", "")
                        .replaceAll("^/tmp/", "")
        );

        // If we're running locally, use the source tree version instead of copied classes
        File local = new File(Path.of("src/main/resources/" + resourcePath.toString())
                .toAbsolutePath().toString());
        if (local.exists()) return local;

        // Otherwise, it could be in a jar, make a local copy, benefit is that this
        // is now editable and reloadable (probably better way to handle this)
        if (path.startsWith("/tmp")) return path.toFile();
        InputStream is = Wrapper.class.getClassLoader().getResourceAsStream(resourcePath.toString());
        try {
            return copy(resourcePath.toString(), is.readAllBytes());
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }
    public static File standardResource(File file) {
        if (file.toString().startsWith("resources/pixelblaze/__pbb_")) {
            String scriptName = file.toString().substring(27, file.toString().length() - 3);
            return copy("resources/pixelblaze/" + scriptName + ".js", patternData.get(scriptName).getBytes(StandardCharsets.UTF_8));
        }
        return standardResource(file.toPath());
    }

    public static void onLoad(Bindings bindings, CompiledScript glue, CompiledScript pattern, Wrapper wrapper) {
        try {
            PixelblazePatterns.extraGlueScript = Wrapper.compile(Path.of("resources/pixelblaze/moarPaste.js"));
            PixelblazePatterns.extraGlueScript.eval(bindings);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    public static void onPostLoad(Bindings bindings, CompiledScript glue, CompiledScript patternScript, Wrapper wrapper, LXPattern lxPattern) {
        if (lxPattern instanceof PixelBlazeBlowser) {
            PixelBlazeBlowser pattern = ((PixelBlazeBlowser) lxPattern);
            if (pattern.onReload != null) {
                pattern.onReload.bang();
                pattern.scriptName.setValue(pattern.getScriptName(), true);
            }
        }
    }

    public static void onRender(Bindings bindings, double deltaMs, int[] colors, Wrapper wrapper) {
        bindings.put("energyAverage", Audio.get().teEngine.volumeLevel);
        bindings.put("frequencyData", Audio.get().teEngine.eq.getSamples());
        // todo: actually detect note (chroma?), faking saw tooth vol + chromatic note cycle over 126 bpm
        double timeStep = Audio.now() / (1_000. * 60. / 126.);
        bindings.put("maxFrequency", Math.pow(2., (timeStep / 12.) % 12.) * 220.);
        bindings.put("maxFrequencyMagnitude", timeStep - Math.floor(timeStep));

        try {
            PixelblazePatterns.extraGlueScript.eval(bindings);
        } catch (Exception e) {
            throw new RuntimeException(e);
        }
    }

    private static File copy(String resourcePath, byte[] content) {
        Path tmpFile = Path.of("/tmp/" + resourcePath);
        try {
            Files.createDirectories(tmpFile.getParent());
            Files.write(tmpFile, content, StandardOpenOption.CREATE, StandardOpenOption.WRITE);
            return new File(tmpFile.toAbsolutePath().toString());
        } catch (Throwable e) {
            throw new RuntimeException(e);
        }
    }

    private static void addPixelblazeDownloads(Map<String, String> nameToSource) {
        Map<String, String> sorted = new TreeMap<>();
        ClassLoader classLoader = PixelblazePatterns.class.getClassLoader();

        // Specify the directory in the resources folder
        String resourceDirectory = "pixelblaze-patterns"; // Replace with your resource directory

        try {
            // Get the URL of the resource directory
            URL resourceDirURL = classLoader.getResource(resourceDirectory);

            if (resourceDirURL != null) {
                URI uri = resourceDirURL.toURI();
                Path resourceDirPath;
                if (uri.getScheme().equals("jar")) {
                    FileSystem fileSystem = FileSystems.newFileSystem(uri, Collections.emptyMap());
                    resourceDirPath = fileSystem.getPath(resourceDirectory);
                } else {
                    resourceDirPath = Paths.get(uri);
                }

                Files.walkFileTree(resourceDirPath, new SimpleFileVisitor<>() {
                    @Override
                    public FileVisitResult visitFile(Path entry, BasicFileAttributes attrs) throws IOException {
                        String file = entry.toAbsolutePath().toString().replaceAll(resourceDirPath.toAbsolutePath().toString(), "");
                        String src = null;
                        if (file.endsWith(".epe")) {
                            src = gson.fromJson(Files.readString(entry), JsonObject.class)
                                    .get("sources")
                                    .getAsJsonObject()
                                    .get("main")
                                    .getAsString();
                        }
                        else if (file.endsWith(".js")) {
                            src = Files.readString(entry);
                        }
                        else {
                            System.out.println("SKIPPING PIXELBLAZE unknown: " + file);
                        }

                        if (nameToSource.containsKey(file) || sorted.containsKey(file)) {
                            System.out.println("SKIPPING DUPLICATE PIXELBLAZE: " + file);
                        } else if (src != null) {
                            System.out.println("Loading pixelblaze extra: " + file);
                            sorted.put(file, src);
                        }

                        return FileVisitResult.CONTINUE;
                    }
                });
            } else {
                System.out.println("Resource directory not found");
            }
        } catch (Exception e) {
            e.printStackTrace();
        }

        nameToSource.putAll(sorted);
    }

    private static Map<String, String> loadPatternData() {
        try {
            InputStream is = PixelblazePatterns.class.getClassLoader()
                    .getResourceAsStream("patternData.json.gz");
            JsonArray patternData = gson.fromJson(new InputStreamReader(new GZIPInputStream(is)), JsonArray.class);
            Map<String, String> nameToSource = new LinkedHashMap<>();
            StreamSupport.stream(patternData.spliterator(), false)
                    .map(el -> (JsonObject) el)
                    .forEach(el -> nameToSource.put(
                            el.get("name").getAsString(),
                            el.get("file").getAsJsonObject()
                                .get("sources").getAsJsonObject()
                                .get("main").getAsString()));
            addPixelblazeDownloads(nameToSource);
            return nameToSource;
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    /** Maybe this was meant to set and  */
    @LXCategory("PixelBlaze") public static class PBTemp extends PixelblazeHelper
    { public PBTemp(LX lx) { super(lx); } public String getScriptName() { return "tmp"; } }
}
