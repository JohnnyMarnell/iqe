/**
 * Ported from the amazing PixelBlaze and Titanic's End work
 * https://github.com/titanicsend/LXStudio-TE
 * Thank you Ben H + Jeff V + Mark Slee!
 */

package titanicsend.pattern;

import heronarts.lx.LX;
import heronarts.lx.color.LXColor;
import heronarts.lx.pattern.LXPattern;
import heronarts.lx.utils.LXUtils;
import titanicsend.pattern.pixelblaze.TEShaderView;

public abstract class PortFacade_TEPerformancePattern extends LXPattern {
    public PortFacade_TEPerformancePattern(LX lx) {
        super(lx);
    }

    public PortFacade_TEPerformancePattern(LX lx, TEShaderView foo) {
        this(lx);
    }


    // Return a color along the HSB wheel between Cyan and Magenta, :shrug-ebroji:
    public int getGradientColor(float lerp) {
        return LXColor.hsb(LXUtils.lerp(180, 300, lerp), 100., 100.);
    }

    public static long startTimeMs;
    public double getTime() {
        if (startTimeMs == 0) startTimeMs = getTimeMs();
        return (getTimeMs() - startTimeMs) / 1_000.;
    }
    public long getTimeMs() {
        return getLX().engine.nowMillis;
    }
    public double getXPos() { return 0.; }
    public double getYPos() { return 0.; }
    public void clearPixels() { }
    public void addCommonControls() { }

    protected abstract void runTEAudioPattern(double deltaMs);
    @Override
    protected void run(double deltaMs) {
        runTEAudioPattern(deltaMs);
    }
}
