package org.iqe.pattern.pixelblaze;

import heronarts.lx.LX;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.transform.LXMatrix;
import heronarts.lx.utils.LXUtils;
import heronarts.lx.utils.Noise;
import org.iqe.LOG;
import titanicsend.TEMath;
import titanicsend.pattern.pixelblaze.PixelblazePattern;

import java.time.LocalDateTime;

/**
 * Further scaffolding to be able to render Pixelblaze animations in LX
 * Attempt to encapsulate any additional logic and state necessary (e.g. pertaining to transformations, gradients)
 * Favor moving / keeping things in this Java realm, over JS scripting like glue.js approach,
 * mainly for ability to debug, probably speed improvements as well?
 * Doesn't need to extend LXPattern or similar, but does at present since existing port sets up __pattern etc.
 *
 * todo: Based on logs, the PB parameters seem to be removed and re-added, however UI doesn't update with knobs
 * todo: impl palette / color / gradient
 * todo: how should transforms truly work (i.e. wouldn't LXPoint -> color buffer index need to change / re-map?)
 * todo: sinpulse 3D and fast pulse 3D aren't rendering anything, why?
 */
public class PixelblazeHelper extends PixelblazePattern {
    protected LXPoint[] originalPoints;
    protected LXPoint[] transformedPoints;

    protected LXMatrix transform = new LXMatrix();
    protected boolean transformNeeded = false;
    protected int perlinWrapX, perlinWrapY, perlinWrapZ;

    public PixelblazeHelper(LX lx) {
        super(lx);
        reset();
    }

    public void beforeRender(float deltaMs, long now, LXPoint[] points, int[] colors) {
        // Pixelblaze JS uses normalized values, so manually transform those
        if (transformNeeded) {
            for (int i = 0; i < transformedPoints.length; i++) {
                LXPoint t = transformedPoints[i];
                LXPoint o = originalPoints[i];
                t.xn = transform.m11 * o.xn + transform.m12 * o.yn + transform.m13 * o.zn + transform.m14;
                t.yn = transform.m21 * o.xn + transform.m22 * o.yn + transform.m23 * o.zn + transform.m24;
                t.zn = transform.m31 * o.xn + transform.m32 * o.yn + transform.m33 * o.zn + transform.m34;
            }
            transformNeeded = false;
        }
    }

    public void reset() {
        if (originalPoints != null) {
            for (int i = 0; i < originalPoints.length; i++) {
                transformedPoints[i].set(originalPoints[i]);
            }
        }
        transform.identity();
        transformNeeded = false;
        perlinWrapX = perlinWrapY = perlinWrapZ = 256;
    }

    @Override
    protected String getScriptName() {
        throw new UnsupportedOperationException("This part of functionality shouldn't be used.");
    }

    @Override
    public LXPoint[] getModelPoints() {
        if (originalPoints == null) {
            originalPoints = super.getModelPoints();
            transformedPoints = new LXPoint[originalPoints.length];
            for (int i = 0; i < transformedPoints.length; i++) {
                transformedPoints[i] = new LXPoint(originalPoints[i]);
            }
        }
        return transformedPoints;
    }

    @Override
    public void addSlider(String key, String label) {
        LOG.info("Add slider called for key '{}', label '{}'", key, label);
        super.addSlider(key, label);
    }

    @Override
    public double getSlider(String key) {
        return super.getSlider(key);
    }

    public void resetTransform() {
        transform.identity();
        transformNeeded = true;
    }

    public void scale(float x, float y, float z) {
        transform.scale(x, y, z);
        transformNeeded = true;
    }

    public void translate(float x, float y, float z) {
        transform.translate(x, y, z);
        transformNeeded = true;
    }

    public double perlinRidge(float x, float y, float z, float lacunarity, float gain, float offset, int octaves) {

        return LXNoisePorted.stb_perlin_ridge_noise3(x, y, z,
                lacunarity, gain, offset, octaves,
                perlinWrapX, perlinWrapY, perlinWrapZ);

    }

    public double perlinTurbulence(float x, float y, float z, float lacunarity, float gain, int octaves) {
        return LXNoisePorted.stb_perlin_turbulence_noise3(
                x, y, z, lacunarity, gain, octaves,
                perlinWrapX, perlinWrapY, perlinWrapZ);
    }

    public void setPerlinWrap(int x, int y, int z) {
        perlinWrapX = x;
        perlinWrapY = y;
        perlinWrapZ = z;
    }

    public double smoothstep(double min, double max, double val) {
        return TEMath.smoothstep(min, max, val);
    }

    // todo: impl and use the PB script setPalette()
    public void setPalette(float[] array) {

    }

    // todo: impl and use the PB script setPalette()
    @Override
    public int getGradientColor(float lerp) {
        return LXColor.hsb(LXUtils.lerp(180, 300, lerp), 100., 100.);
    }

    // todo: impl and use the PB script setGradient()
    public int paint(float lerp, float brightness) {
        return getGradientColor(lerp);
    }

    public int clockYear() {
        return LocalDateTime.now().getYear();
    }

    public int clockMonth() {
        return LocalDateTime.now().getMonthValue();
    }

    public int clockDay() {
        return LocalDateTime.now().getDayOfMonth();
    }

    public int clockWeekday() {
        int mondayOneIndexed = LocalDateTime.now().getDayOfWeek().getValue();
        return ((((7 + mondayOneIndexed - 1) % 7) + 8) % 7) + 1;
    }

    public int clockHour() {
        return LocalDateTime.now().getHour();
    }

    public int clockMinute() {
        return LocalDateTime.now().getMinute();
    }

    public int clockSecond() {
        return LocalDateTime.now().getSecond();
    }

    public void log(String msg) {
        LOG.info(msg);
    }

    // idk what to do for these:
    public void pinMode(int pin, int mode) {

    }
}