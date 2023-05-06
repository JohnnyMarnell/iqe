package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.parameter.EnumParameter;
import heronarts.lx.structure.StripFixture;

@LXCategory("IQE")
public class NagBugglerSaberOfLightFixture extends StripFixture {
    public static enum Kind {
        PILLAR,
        RAFTER
    }
    public final EnumParameter<Kind> kind = new EnumParameter<>("Kind", Kind.PILLAR)
            .setDescription("What kind / purpose / location of this strip, e.g. a pillar / pole");

    public NagBugglerSaberOfLightFixture(LX lx) {
        super(lx);
        init();
    }

    /**
     * Each of our customer strip is the same, so use those values (way to lock these?)
     */
    protected void init() {
//        System.out.println("*************** test");
        numPoints.setValue(140, true);
        spacing.setValue(5, true);
        kind.setValue(Kind.PILLAR);

        // todo protocol and its params / details
    }

}
