package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.structure.PointListFixture;
import heronarts.lx.structure.StripFixture;
import heronarts.lx.transform.LXVector;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

public class FlamecasterFixtures {

    public static final int MAX_PIXELS_PER_UNIVERSE = 170;

    public static final float VERT_SPACE = 100.0f;
    public static final float HORIZ_SPACE = 20.0f;

    public static class NECorner extends FlamecasterNetFixture {
        public NECorner(LX lx) {
            super(lx, 6455 + 0);
            LOG.info("NECorner start main construct sigh");

//            var strip = new StripFixture(lx);
//
//            strip.x.setValue(0);
//            strip.y.setValue(0);
//            strip.z.setValue(0);
//
//            strip.numPoints.setValue(200);
//            strip.spacing.setValue(VERT_SPACE);
//
//            strip.protocol.setValue(Integer.valueOf(Protocol.ARTNET.ordinal()).doubleValue()); // lulz?
//            strip.port.setValue(flamecasterPort);
//            strip.byteOrder.setValue(Integer.valueOf(LXBufferOutput.ByteOrder.RGB.ordinal()).doubleValue()); // sigh?
//            strip.artNetUniverse.setValue(4096);
//            strip.dmxChannel.setValue(channel);
//            strip.enabled.setValue(true);
//
//            this.addChild(strip, true);

            drape(-9.5f * HORIZ_SPACE, 0);
//            drape(-8.5f * HORIZ_SPACE, 0);
//            drape(-7.5f * HORIZ_SPACE, 0);
//            drape(-6.5f * HORIZ_SPACE, 0);
//            drape(-5.5f * HORIZ_SPACE, 0);
//            drape(-4.5f * HORIZ_SPACE, 0);
//            drape(-3.5f * HORIZ_SPACE, 0);
//            drape(-2.5f * HORIZ_SPACE, 0);
//            drape(-1.5f * HORIZ_SPACE, 0);
//            drape(-0.5f * HORIZ_SPACE, 0);
//
//            drape(0, -0.5f * HORIZ_SPACE);
//            drape(0, -1.5f * HORIZ_SPACE);
//            drape(0, -2.5f * HORIZ_SPACE);
//            drape(0, -3.5f * HORIZ_SPACE);
//            drape(0, -4.5f * HORIZ_SPACE);
//            drape(0, -5.5f * HORIZ_SPACE);
//            drape(0, -6.5f * HORIZ_SPACE);
//            drape(0, -7.5f * HORIZ_SPACE);
//            drape(0, -8.5f * HORIZ_SPACE);
//            drape(0, -9.5f * HORIZ_SPACE);

            LOG.info("NECorner exit construct sigh");
        }
    }

    public static class NWCorner extends FlamecasterNetFixture {
        public NWCorner(LX lx) {
            super(lx, 6455 + 1);
            LOG.info("NWCorner start main construct sigh");

             drape(0, 9.5f * HORIZ_SPACE);
//             drape(0, 8.5f * HORIZ_SPACE);
//             drape(0, 7.5f * HORIZ_SPACE);
//             drape(0, 6.5f * HORIZ_SPACE);
//             drape(0, 5.5f * HORIZ_SPACE);
//             drape(0, 4.5f * HORIZ_SPACE);
//             drape(0, 3.5f * HORIZ_SPACE);
//             drape(0, 2.5f * HORIZ_SPACE);
//             drape(0, 1.5f * HORIZ_SPACE);
//             drape(0, 0.5f * HORIZ_SPACE);
//
//             drape(-0.5f * HORIZ_SPACE, 0);
//             drape(-1.5f * HORIZ_SPACE, 0);
//             drape(-2.5f * HORIZ_SPACE, 0);
//             drape(-3.5f * HORIZ_SPACE, 0);
//             drape(-4.5f * HORIZ_SPACE, 0);
//             drape(-5.5f * HORIZ_SPACE, 0);
//             drape(-6.5f * HORIZ_SPACE, 0);
//             drape(-7.5f * HORIZ_SPACE, 0);
//             drape(-8.5f * HORIZ_SPACE, 0);
//             drape(-9.5f * HORIZ_SPACE, 0);

            LOG.info("NWCorner exit main construct sigh");
        }
    }

    public static class FlamecasterNetFixture extends PointListFixture {
        int pixelsMapped = 0;
        int flamecasterPort;

        int universe = 0;
        int channel = 0;

        public FlamecasterNetFixture(LX lx, int port) {
            super(lx, Collections.emptyList());
//            LOG.info("sigh FC postContruct");
            flamecasterPort = port;
        }

        // TODO (jmarnell): handle variable pixels, split across strips / fixtures
        protected void drape(float x, float z) {
            int numPixels = 10;
            assert pixelsMapped + numPixels <= MAX_PIXELS_PER_UNIVERSE : "todo, split across fixtures";

//            StripFixture strip = new StripFixture(lx);
            StripFixture strip = new OOPIsDead(lx, flamecasterPort);

            strip.x.setValue(x);
            strip.y.setValue(this.y.getValuef());
            strip.z.setValue(z);

            strip.numPoints.setValue(numPixels);
            strip.spacing.setValue(VERT_SPACE);

            strip.protocol.setValue(Integer.valueOf(Protocol.ARTNET.ordinal()).doubleValue()); // lulz?
            strip.artNetUniverse.setValue(universe);
            strip.dmxChannel.setValue(channel);
            strip.enabled.setValue(true);
            strip.port.setValue(flamecasterPort);

            this.addChild(strip);
//            this.addChild(strip, true);
//            org.iqe.LXUtils.addChildRegen(this, strip);

            pixelsMapped += numPixels;
            channel += numPixels;
            if (pixelsMapped % MAX_PIXELS_PER_UNIVERSE == 0) {
                universe++;
                channel = 0;
            }
        }

        @Override
        protected void buildOutputs() {
//            LOG.info("sigh, FC buildOutputs1 {} {}", protocol.getEnum(), port.getValuei());
            super.buildOutputs();
//            children.forEach(c -> c.buildOutputs()); // so effing annoying, protected
//            LOG.info("sigh, FC buildOutputs2 {} {}", protocol.getEnum(), port.getValuei());
        }

        @Override
        protected void beforeRegenerate() {
//            LOG.info("sigh, FC beforeRegen {} {}", protocol.getEnum(), port.getValuei());
            super.beforeRegenerate();
        }
    }

    public static List<LXVector> points2() {
        var points = new ArrayList<LXVector>();

        // down(points, -0.5f * HORIZ_SPACE, 0);
        // down(points, -1.5f * HORIZ_SPACE, 0);
        // down(points, -2.5f * HORIZ_SPACE, 0);
        // down(points, -3.5f * HORIZ_SPACE, 0);
        // down(points, -4.5f * HORIZ_SPACE, 0);
        // down(points, -5.5f * HORIZ_SPACE, 0);
        // down(points, -6.5f * HORIZ_SPACE, 0);
        // down(points, -7.5f * HORIZ_SPACE, 0);
        // down(points, -8.5f * HORIZ_SPACE, 0);
        // down(points, -9.5f * HORIZ_SPACE, 0);
        //
        // down(points, 0, -0.5f * HORIZ_SPACE);
        // down(points, 0, -1.5f * HORIZ_SPACE);
        // down(points, 0, -2.5f * HORIZ_SPACE);
        // down(points, 0, -3.5f * HORIZ_SPACE);
        // down(points, 0, -4.5f * HORIZ_SPACE);
        // down(points, 0, -5.5f * HORIZ_SPACE);
        // down(points, 0, -6.5f * HORIZ_SPACE);
        // down(points, 0, -7.5f * HORIZ_SPACE);
        // down(points, 0, -8.5f * HORIZ_SPACE);
        // down(points, 0, -9.5f * HORIZ_SPACE);

        return points;
    }

    public static List<LXVector> points() {
        var points = new ArrayList<LXVector>();

        // down(points, -0.5f * HORIZ_SPACE);
        // down(points, -1.5f * HORIZ_SPACE);
        // down(points, -2.5f * HORIZ_SPACE);
        // down(points, -3.5f * HORIZ_SPACE);
        // down(points, -4.5f * HORIZ_SPACE);
        // down(points, -5.5f * HORIZ_SPACE);
        // down(points, -6.5f * HORIZ_SPACE);
        // down(points, -7.5f * HORIZ_SPACE);
        // down(points, -8.5f * HORIZ_SPACE);
        // down(points, -9.5f * HORIZ_SPACE);
        //
        // down(points, 0, 0.5f * HORIZ_SPACE);
        // down(points, 0, 1.5f * HORIZ_SPACE);
        // down(points, 0, 2.5f * HORIZ_SPACE);
        // down(points, 0, 3.5f * HORIZ_SPACE);
        // down(points, 0, 4.5f * HORIZ_SPACE);
        // down(points, 0, 5.5f * HORIZ_SPACE);
        // down(points, 0, 6.5f * HORIZ_SPACE);
        // down(points, 0, 7.5f * HORIZ_SPACE);
        // down(points, 0, 8.5f * HORIZ_SPACE);
        // down(points, 0, 9.5f * HORIZ_SPACE);

        return points;
    }

    // strip.host.setValue("127.0.0.1");

    // strip = new StripFixture(lx);
    // strip.x.setValue(10);
    // strip.numPoints.setValue(7);
    // strip.artNetUniverse.setValue(0);
    // strip.protocol.setValue(Integer.valueOf(Protocol.ARTNET.ordinal()).doubleValue());
    // strip.dmxChannel.setValue(0);
    // strip.enabled.setValue(true);
    // strip.port.setValue(6454);
    // addChild(strip, true);
    //
    // strip = new StripFixture(lx);
    // strip.numPoints.setValue(7);
    // strip.artNetUniverse.setValue(1);
    // strip.protocol.setValue(Integer.valueOf(Protocol.ARTNET.ordinal()).doubleValue());
    // strip.dmxChannel.setValue(0);
    // strip.enabled.setValue(true);
    // strip.port.setValue(6454);
    // addChild(strip, true);

    public static class OOPIsDead extends PatchedStripFixture { public OOPIsDead(LX lx, int p) { super(lx, p); } public OOPIsDead(LX lx) { super(lx); } }
    public static class PatchedStripFixture extends StripFixture {

        public PatchedStripFixture(LX lx) {
            this(lx, 6454);
        }

        public PatchedStripFixture(LX lx, int realPort) {
            super(lx);
            this.port.setValue(realPort);
        }

        @Override
        protected void buildOutputs() {
//            LOG.info("sigh, buildOutputs1 {} {}", protocol.getEnum(), port.getValuei());
            super.buildOutputs();
            logStatus();
//            LOG.info("sigh, buildOutputs2 {} {}", protocol.getEnum(), port.getValuei());
        }

        public void logStatus() {
            outputDefinitions.forEach(o -> {
                LOG.info("{} output OOPisded universe {} port {}",
                        this.getLabel(),
                        LXUtils.field(o, "universe"),
                        LXUtils.field(o, "port"));
            });
        }

        @Override
        protected Segment buildSegment() {
//            LOG.info("sigh, buildSegment1 {} {}", protocol.getEnum(), port.getValuei());
            var segFault = super.buildSegment();
//            LOG.info("sigh, buildSegment2 {} {}", protocol.getEnum(), port.getValuei());
            return segFault;
        }

        @Override
        protected void beforeRegenerate() {
//            LOG.info("sigh, beforeRegen {} {}", protocol.getEnum(), port.getValuei());
            super.beforeRegenerate();
        }

        @Override
        protected int getProtocolPort() {
            var port = super.getProtocolPort();
            LOG.info("so dumb, always protocol port sigh {} remap hopefully to {}", port, this.port.getValuei());
            return this.port.getValuei();
        }
    }
}
