package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.parameter.EnumParameter;
import heronarts.lx.parameter.StringParameter;
import heronarts.lx.structure.StripFixture;

@LXCategory("IQE")
public class NagBugglerLightSaber extends StripFixture {
    public static enum Kind {
        PILLAR_LEFT,
        PILLAR_MIDDLE,
        PILLAR_RIGHT,
        RAFTER_SUPPLY,
        RAFTER_DEMAND,
        RAFTER_PERIMETER_X,
        RAFTER_PERIMETER_Z,
        RAFTER_INNER_X
    }
    public final EnumParameter<Kind> kind = new EnumParameter<>("Kind", Kind.PILLAR_LEFT)
            .setDescription("What kind / purpose / location of this strip, e.g. a pillar / pole");

    public NagBugglerLightSaber(LX lx) {
        super(lx);
        init();
    }

    /**
     * Each of our customer strip is the same, so use those values (way to lock these?)
     */
    protected void init() {
        System.out.println("***************I test");
        numPoints.setValue(140, true);
        spacing.setValue(5, true);
        kind.setValue(Kind.PILLAR_LEFT);

        // todo protocol and its params / details
    }


}
