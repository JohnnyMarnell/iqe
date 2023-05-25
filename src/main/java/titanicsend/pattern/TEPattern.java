/**
 * Ported from the amazing PixelBlaze and Titanic's End work
 * https://github.com/titanicsend/LXStudio-TE
 * Thank you Ben H + Jeff V + Mark Slee!
 */

package titanicsend.pattern;

import heronarts.lx.LX;
import heronarts.lx.pattern.LXPattern;

public class TEPattern extends LXPattern {

    public enum ColorType {
        // These are 1-based UI indices; to get to a 0-based palette swatch index, subtract 1
        BACKGROUND(1), // Background color - should usually be black or transparent
        TRANSITION(2), // Transitions a background to the primary, commonly just the background again
        PRIMARY(3),    // Primary color of any edge or panel pattern
        SECONDARY(4),  // Secondary color; optional, commonly set to SECONDARY_BACKGROUND or PRIMARY
        SECONDARY_BACKGROUND(5);  // Background color if transitioning from SECONDARY. Commonly set to same color as BACKGROUND.

        public final int index;  // The UI index (1-indexed)
        private ColorType(int index) {
            this.index = index;
        }

        // UI swatches are 1-indexed; internally, swatch arrays are 0-indexed
        public int swatchIndex() {
            return index - 1;
        }
    }

    public TEPattern(LX lx) {
        super(lx);
    }

    @Override
    protected void run(double v) {
        throw new UnsupportedOperationException("We shouldn't really be using this");
    }
}
