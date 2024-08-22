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

    /* Tied to VERY persnickety, and buggy ArtNet outputs per Fixture mechanism.
    *  Thus using strips of size 10 */
    public static final int FIXTURE_PIXEL_INCREMENT = 10;

    public static final float VERT_SPACE = 100.0f;
    public static final float HORIZ_SPACE = 20.0f;

    public static class NECorner extends FlamecasterNetFixture {
        public NECorner(LX lx) {
            super(lx, 6455, 200, 0);
            LOG.info("NECorner start main construct sigh");
            this.label.setValue("NECorner");

            drape(-9.5f * HORIZ_SPACE, 0);
            drape(-8.5f * HORIZ_SPACE, 0);
            drape(-7.5f * HORIZ_SPACE, 0);
            drape(-6.5f * HORIZ_SPACE, 0);
            drape(-5.5f * HORIZ_SPACE, 0);
            drape(-4.5f * HORIZ_SPACE, 0);
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

            LOG.info("NECorner exit construct sigh, pixelsMapped {}", pixelsMapped);
        }
    }

    public static class NWCorner extends FlamecasterNetFixture {
        public NWCorner(LX lx) {
            super(lx, 6455, 400, 2);
            LOG.info("NWCorner start main construct sigh");
            this.label.setValue("NWCorner");

             drape(0, 9.5f * HORIZ_SPACE);
             drape(0, 8.5f * HORIZ_SPACE);
             drape(0, 7.5f * HORIZ_SPACE);
             drape(0, 6.5f * HORIZ_SPACE);
             drape(0, 5.5f * HORIZ_SPACE);
             drape(0, 4.5f * HORIZ_SPACE);
             drape(0, 3.5f * HORIZ_SPACE);
             drape(0, 2.5f * HORIZ_SPACE);
             drape(0, 1.5f * HORIZ_SPACE);
             drape(0, 0.5f * HORIZ_SPACE);

             drape(-0.5f * HORIZ_SPACE, 0);
             drape(-1.5f * HORIZ_SPACE, 0);
             drape(-2.5f * HORIZ_SPACE, 0);
             drape(-3.5f * HORIZ_SPACE, 0);
             drape(-4.5f * HORIZ_SPACE, 0);
             drape(-5.5f * HORIZ_SPACE, 0);
//             drape(-6.5f * HORIZ_SPACE, 0);
//             drape(-7.5f * HORIZ_SPACE, 0);
//             drape(-8.5f * HORIZ_SPACE, 0);
//             drape(-9.5f * HORIZ_SPACE, 0);

            LOG.info("NWCorner exit main construct sigh, pixelsMapped {}", pixelsMapped);
        }
    }

    /***
     * Each Flamecaster fixture needs to count pixelsMapped, and increment sub-fixture
     * universes and channels in properly striped manner.
     *
     * They must be defined in contiguous order, to match Flamecaster config.
     */
    public static class FlamecasterNetFixture extends PointListFixture {
        protected static int pixelsMapped = 0;

        int universe;
        int totalPixelsInThisFixture;

        int channel = 0;
        int pixelsMappedInThisFixture = 0;
        int flamecasterPort;

        public FlamecasterNetFixture(LX lx, int port, int totalPixelsInThisFixture, int startingUniverse) {
            super(lx, Collections.emptyList());
//            LOG.info("sigh FC postContruct");
            this.flamecasterPort = port;
            this.totalPixelsInThisFixture = totalPixelsInThisFixture;
            this.universe = startingUniverse;
        }

        // The curtain / nets drape down 20 pixels
        protected void drape(float x, float z) {
            strip(x, z, this.y.getValuef(), FIXTURE_PIXEL_INCREMENT, VERT_SPACE);
            strip(x, z, this.y.getValuef() - FIXTURE_PIXEL_INCREMENT * VERT_SPACE, FIXTURE_PIXEL_INCREMENT, VERT_SPACE);
        }

        // TODO (jmarnell): handle variable pixels, split across strips / fixtures
        protected void strip(float x, float z, float y, int numPixels, float spacing) {
            StripFixture strip = new PatchedStripFixture(lx, flamecasterPort);

            strip.x.setValue(x);
            strip.y.setValue(y);
            strip.z.setValue(z);

            strip.numPoints.setValue(numPixels);
            strip.spacing.setValue(spacing);

            strip.protocol.setValue(Integer.valueOf(Protocol.ARTNET.ordinal()).doubleValue()); // lulz?
            strip.artNetUniverse.setValue(universe);
            strip.dmxChannel.setValue(channel);
            strip.enabled.setValue(true);
            strip.port.setValue(flamecasterPort);

            this.addChild(strip);
//            this.addChild(strip, true);
//            org.iqe.LXUtils.addChildRegen(this, strip);

            countPixels(numPixels);
        }

        protected void countPixels(int numPixels) {
            pixelsMapped += numPixels;
            pixelsMappedInThisFixture += numPixels;

            assert pixelsMappedInThisFixture <= totalPixelsInThisFixture : "too many pixels";

            assert pixelsMapped <= MAX_PIXELS_PER_UNIVERSE : "todo, split across fixtures";

            if (pixelsMapped % MAX_PIXELS_PER_UNIVERSE == 0) {
                universe++;
                channel = 0;
            } else {
                channel += numPixels * 3;
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

    /**
     * Uncannily, the configured ArtNet port is ignored, it's always the default protocol port...
     */
    public static class PatchedStripFixture extends StripFixture {

        public PatchedStripFixture(LX lx) {
            this(lx, 6455);
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
            FlamecasterNetFixture parent = (FlamecasterNetFixture) this.getParent();
            outputDefinitions.forEach(o -> {
                LOG.info("{} output OOPisded port {} universe {} chan {}, so far {}",
                        this.getParent().getLabel(),
                        LXUtils.field(o, "port"),
                        LXUtils.field(o, "universe"),
                        LXUtils.field(o, "channel"),
                        parent.pixelsMappedInThisFixture);
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

        /** THIS IS THE KEY, EVERY FIXTURE TYPE WOULD NEED THIS */
        @Override
        protected int getProtocolPort() {
//            var port = super.getProtocolPort();
//            LOG.info("so dumb, always protocol port sigh {} remap hopefully to {}", port, this.port.getValuei());
            return this.port.getValuei();
        }
    }

    public static class OOPIsDead extends PatchedStripFixture { public OOPIsDead(LX lx, int p) { super(lx, p); } public OOPIsDead(LX lx) { super(lx); } }
}
