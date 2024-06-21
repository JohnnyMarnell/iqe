package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import heronarts.lx.pattern.LXPattern;
import org.iqe.Audio;
import org.iqe.LOG;
import org.iqe.OscBridge;
import org.iqe.Sync;

/***
 * Cycle soloing through model children / fixtures, illuminating orientation, and dump tags
 */
@LXCategory(LXCategory.TEST)
public class DiagnosticColorCyclePattern extends LXPattern {
    private final Sync sync;
    public DiagnosticColorCyclePattern(LX lx) {
        super(lx);
        sync = new Sync(this);
    }

    @Override
    protected void run(double v) {
        // First black out everything
        for (LXPoint p : model.points) colors[p.index] = LXColor.BLACK;

        // Light up a fraction of current fixture (indicates orientation)
        int childIndex = 0;
        float hueIncrement = 360.0f / model.children.length;
        for (LXModel child: model.children) {
            float hue = (childIndex * hueIncrement) % 360;
            int color = LXColor.hsb(hue, 100.0f, 100.0f);

            for (int i = 0; i <= child.points.length - 1; i++) {
                if (childIndex < model.children.length / 2 && i / (double) child.points.length < sync.basis())
                    colors[child.points[i].index] = color;
                else if (childIndex >= model.children.length / 2 && i / (double) child.points.length < sync.basis())
                    colors[child.points[child.points.length - 1 - i].index] = color;
            }

            childIndex++;
        }
    }
}
