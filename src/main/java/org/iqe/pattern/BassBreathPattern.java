package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.audio.GraphicMeter;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXPoint;
import heronarts.lx.parameter.BoundedParameter;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.pattern.LXPattern; import heronarts.lx.utils.LXUtils; import java.util.List;

/**
 * Mostly from ChatGPT, not really useful
 */
public class BassBreathPattern extends LXPattern {
    // Audio input
    final GraphicMeter audioInput;
    // Brightness parameter
    final CompoundParameter brightness = new CompoundParameter("Brightness", 0.2, 0.0, 1.0);
    final BoundedParameter minBand = new BoundedParameter("MinBand", 0.0, 32.0);
    final BoundedParameter numBands = new BoundedParameter("NumBands", 1.0, 32.0);

    public BassBreathPattern(LX lx) {
        super(lx);
        // Get audio input
//        this.audioInput = lx.engine.audio.input;
        this.audioInput = lx.engine.audio.meter;

        // Add the brightness parameter to the LX framework
        addParameter(brightness);
        addParameter(minBand);
        addParameter(numBands);
    }

        @Override public void run(double deltaMs) {
            // Get the bass levels from the audio input
            // double bassLevel = this.audioInput.getBuffer().getFFT().getBand(0);
            // double bassLevel = this.audioInput.getBand(0);
            double bassLevel = this.audioInput.getAverage((int) this.minBand.getValue(), (int) this.numBands.getValue());

            // Map the bass level to a brightness value between 0 and 1
            // double mappedBrightness = LXUtils.map(bassLevel, 0, 10, 0, 1);
            // it already is?
            double mappedBrightness = bassLevel;

            // Apply the brightness parameter to the mapped brightness
            mappedBrightness *= this.brightness.getValue();

            // Initialize the colors array
            // int[] colors = new int[model.size];

            // Get all the points in the model
            //
            LXPoint[] points = model.points;

            // Loop through all the points and set their color based on the mapped brightness
            for (LXPoint p : points) {
                // this.colors[p.index] = LXColor.gray(mappedBrightness * 100);
                this.colors[p.index] = LXColor.hsb(240, 100, 60 + mappedBrightness * 40);
            }
        }
    }