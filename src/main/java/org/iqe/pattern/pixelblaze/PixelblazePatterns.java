package org.iqe.pattern.pixelblaze;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.model.LXPoint;
import titanicsend.pattern.PortFacade_TEPerformancePattern;
import titanicsend.pattern.pixelblaze.PixelblazePattern;
import titanicsend.pattern.pixelblaze.Wrapper;

import java.io.File;
import java.io.IOException;
import java.net.URL;
import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * I'm all inheritance / .class'd out y'all...
 */

public class PixelblazePatterns {

    public static class PixelBlazeBlowser extends PixelblazePattern {
        public PixelBlazeBlowser(LX lx) {
            super(lx);
        }

        @Override
        protected String getScriptName() {
            throw new UnsupportedOperationException("Hacking around more inheritance");
        }
    }

    public static Wrapper wrapper(String pbClass, PortFacade_TEPerformancePattern pattern, LXPoint[] points) throws Exception {
        return null;
    }

    // todo: automate all of these
    // todo: use .epe file directly, or write script to preprocess
    // todo: instead of 600+ patterns to be added, one dynamic one, with an LXParameter dropdown to select / re-compile
    //          if necessary?
    @LXCategory("PixelBlaze") public static class Fireflies extends PBP
    { public Fireflies(LX lx) { super(lx); } public String getScriptName() { return "FireFlies.epe"; } }

    @LXCategory("PixelBlaze") public static class RegenBogenDrogenMyBrogans extends PBP
    { public RegenBogenDrogenMyBrogans(LX lx) { super(lx); } public String getScriptName() { return "regenbogendrogen.epe"; } }

    public static abstract class PBP extends PixelblazePattern {
        public PBP(LX lx) {
            super(lx);
        }
    }

    // Johnny Marnell port:
    // Proper java structure package uses src/main/resources directory, removing redundant + breaking prepend
    public static File standardResource(Path path) throws IOException {
        Path resourcePath = Path.of(
                path.toString().replaceAll("resources/", "")
                        .replaceAll("^.*classes/", "")
        );
        URL url = Wrapper.class.getClassLoader().getResource(resourcePath.toString());
        try {
            return new File(Paths.get(url.toURI()).toAbsolutePath().toString());
        } catch (Throwable e) {
            throw new IOException(e);
        }
    }
}
