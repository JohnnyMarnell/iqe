package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.structure.LXFixture;
import heronarts.lx.structure.PointListFixture;
import heronarts.lx.structure.StripFixture;
import heronarts.lx.transform.LXVector;

import java.util.ArrayList;
import java.util.List;

public class CornerFixture extends PointListFixture {

    public static final float VERT_SPACE = 100.0f;
    public static final float HORIZ_SPACE = 20.0f;


    public CornerFixture(LX lx) {
        super(lx, points());
        StripFixture strip = new StripFixture(lx);
        strip.numPoints.setValue(1000);
        strip.protocol.setValue(Integer.valueOf(Protocol.ARTNET.ordinal()).doubleValue());
        strip.artNetUniverse.setValue(3);
        strip.dmxChannel.setValue(5);
        strip.enabled.setValue(true);
        strip.port.setValue(6454);
        addChild(strip);
//        this.protocol.setValue(Integer.valueOf(Protocol.ARTNET.ordinal()).doubleValue());
//        this.protocol.setValue(Protocol.ARTNET);
//        this.artNetUniverse.setValue(1);
//        this.dmxChannel.setValue(0);
    }

    @Override
    protected void buildOutputs() {
//        this.protocol.setValue(Integer.valueOf(Protocol.ARTNET.ordinal()).doubleValue());
        LOG.info("BUILD OUTPUTS");
        super.buildOutputs();
    }

    public static List<LXVector> points() {
        var points = new ArrayList<LXVector>();

        down(points, -0.5f * HORIZ_SPACE, 0);
        down(points, -1.5f * HORIZ_SPACE, 0);
        down(points, -2.5f * HORIZ_SPACE, 0);
        down(points, -3.5f * HORIZ_SPACE, 0);
        down(points, -4.5f * HORIZ_SPACE, 0);
        down(points, -5.5f * HORIZ_SPACE, 0);
        down(points, -6.5f * HORIZ_SPACE, 0);
        down(points, -7.5f * HORIZ_SPACE, 0);
        down(points, -8.5f * HORIZ_SPACE, 0);
        down(points, -9.5f * HORIZ_SPACE, 0);

        down(points, 0, -0.5f * HORIZ_SPACE);
        down(points, 0, -1.5f * HORIZ_SPACE);
        down(points, 0, -2.5f * HORIZ_SPACE);
        down(points, 0, -3.5f * HORIZ_SPACE);
        down(points, 0, -4.5f * HORIZ_SPACE);
        down(points, 0, -5.5f * HORIZ_SPACE);
        down(points, 0, -6.5f * HORIZ_SPACE);
        down(points, 0, -7.5f * HORIZ_SPACE);
        down(points, 0, -8.5f * HORIZ_SPACE);
        down(points, 0, -9.5f * HORIZ_SPACE);

        return points;
    }

    public static void down(List<LXVector> points, float x, float z) {
        for (int i = 0; i < 10; i++) {
            points.add(new LXVector(x, i * -VERT_SPACE, z));
        }
    }

    public static class OtherCorner extends PointListFixture {
        public OtherCorner(LX lx) {
            super(lx, points());
//            this.protocol.setValue(Integer.valueOf(Protocol.ARTNET.ordinal()).doubleValue());
//            this.protocol.setValue(Protocol.ARTNET);
//            this.artNetUniverse.setValue(0);
//            this.dmxChannel.setValue(0);

        }

        @Override
        protected void buildOutputs() {
//            this.protocol.setValue(Integer.valueOf(Protocol.ARTNET.ordinal()).doubleValue());
            LOG.info("BUILD OUTPUTS");
            super.buildOutputs();
        }

        public static List<LXVector> points() {
            var points = new ArrayList<LXVector>();

            down(points, -0.5f * HORIZ_SPACE, 0);
            down(points, -1.5f * HORIZ_SPACE, 0);
            down(points, -2.5f * HORIZ_SPACE, 0);
            down(points, -3.5f * HORIZ_SPACE, 0);
            down(points, -4.5f * HORIZ_SPACE, 0);
            down(points, -5.5f * HORIZ_SPACE, 0);
            down(points, -6.5f * HORIZ_SPACE, 0);
            down(points, -7.5f * HORIZ_SPACE, 0);
            down(points, -8.5f * HORIZ_SPACE, 0);
            down(points, -9.5f * HORIZ_SPACE, 0);

            down(points, 0, 0.5f * HORIZ_SPACE);
            down(points, 0, 1.5f * HORIZ_SPACE);
            down(points, 0, 2.5f * HORIZ_SPACE);
            down(points, 0, 3.5f * HORIZ_SPACE);
            down(points, 0, 4.5f * HORIZ_SPACE);
            down(points, 0, 5.5f * HORIZ_SPACE);
            down(points, 0, 6.5f * HORIZ_SPACE);
            down(points, 0, 7.5f * HORIZ_SPACE);
            down(points, 0, 8.5f * HORIZ_SPACE);
            down(points, 0, 9.5f * HORIZ_SPACE);

            return points;
        }
    }
}
