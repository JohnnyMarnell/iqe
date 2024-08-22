package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.structure.PointListFixture;
import heronarts.lx.structure.StripFixture;

import java.util.Collections;

public class FlamecasterFixtures {

    public static final int PIXELS_PER_UNIVERSE = 10;
    public static final int FLAMECASTER_PORT = 6455;

    public static final float VERT_SPACE = 100.0f;
    public static final float HORIZ_SPACE = 20.0f;

    public static class NECorner extends FlamecasterNetFixture {
        public NECorner(LX lx) {
            super(lx);
            LOG.info("NECorner start main construct sigh");

            drape(-9.5f * HORIZ_SPACE, 0);
            drape(-8.5f * HORIZ_SPACE, 0);
            drape(-7.5f * HORIZ_SPACE, 0);
            drape(-6.5f * HORIZ_SPACE, 0);
            drape(-5.5f * HORIZ_SPACE, 0);
            drape(-4.5f * HORIZ_SPACE, 0);
            drape(-3.5f * HORIZ_SPACE, 0);
            drape(-2.5f * HORIZ_SPACE, 0);
            drape(-1.5f * HORIZ_SPACE, 0);
            drape(-0.5f * HORIZ_SPACE, 0);

            drape(0, -0.5f * HORIZ_SPACE);
            drape(0, -1.5f * HORIZ_SPACE);
            drape(0, -2.5f * HORIZ_SPACE);
            drape(0, -3.5f * HORIZ_SPACE);
            drape(0, -4.5f * HORIZ_SPACE);
            drape(0, -5.5f * HORIZ_SPACE);
            drape(0, -6.5f * HORIZ_SPACE);
            drape(0, -7.5f * HORIZ_SPACE);
            drape(0, -8.5f * HORIZ_SPACE);
            drape(0, -9.5f * HORIZ_SPACE);

            LOG.info("NECorner exit construct sigh");
        }
    }

    public static class NWCorner extends FlamecasterNetFixture {
        public NWCorner(LX lx) {
            super(lx);
            LOG.info("NWCorner start main construct sigh");

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
            drape(-6.5f * HORIZ_SPACE, 0);
            drape(-7.5f * HORIZ_SPACE, 0);
            drape(-8.5f * HORIZ_SPACE, 0);
            drape(-9.5f * HORIZ_SPACE, 0);

            LOG.info("NWCorner exit main construct sigh");
        }
    }

    public static class FlamecasterNetFixture extends PointListFixture {
        protected static int universe = 0;

        public FlamecasterNetFixture(LX lx) {
            super(lx, Collections.emptyList());
            this.enabled.setValue(true);
            // LOG.info("sigh FC postContruct");
        }

        protected void drape(float x, float z) {
            strip(x, y.getValuef(), z);
            strip(x, y.getValuef() - PIXELS_PER_UNIVERSE * VERT_SPACE, z);
        }

        // TODO (jmarnell): handle variable pixels, split across strips / fixtures
        protected void strip(float x, float y, float z) {
            // assert pixelsMapped + numPixels <= MAX_PIXELS_PER_UNIVERSE : "todo, split
            // across fixtures";

            // StripFixture strip = new StripFixture(lx);
            StripFixture strip = new OOPIsDead(lx);

            strip.x.setValue(x);
            strip.y.setValue(this.y.getValuef());
            strip.z.setValue(z);

            strip.numPoints.setValue(PIXELS_PER_UNIVERSE);
            strip.spacing.setValue(VERT_SPACE);

            strip.protocol.setValue(Integer.valueOf(Protocol.ARTNET.ordinal()).doubleValue()); // lulz?
            strip.artNetUniverse.setValue(universe);
            strip.dmxChannel.setValue(0);
            strip.enabled.setValue(true);
            this.enabled.setValue(true);

            this.addChild(strip);
            // this.addChild(strip, true);
            // org.iqe.LXUtils.addChildRegen(this, strip);

            universe++;
        }

        @Override
        protected void buildOutputs() {
            // LOG.info("sigh, FC buildOutputs1 {} {}", protocol.getEnum(),
            // port.getValuei());
            super.buildOutputs();
            // children.forEach(c -> c.buildOutputs()); // so effing annoying, protected
            // LOG.info("sigh, FC buildOutputs2 {} {}", protocol.getEnum(),
            // port.getValuei());
        }

        @Override
        protected void beforeRegenerate() {
            // LOG.info("sigh, FC beforeRegen {} {}", protocol.getEnum(), port.getValuei());
            super.beforeRegenerate();
        }
    }

    public static class OOPIsDead extends PatchedStripFixture {

        public OOPIsDead(LX lx) {
            super(lx);
        }
    }

    public static class PatchedStripFixture extends StripFixture {

        public PatchedStripFixture(LX lx) {
            super(lx);
            this.port.setValue(FLAMECASTER_PORT);
        }

        @Override
        protected void buildOutputs() {
            // LOG.info("sigh, buildOutputs1 {} {}", protocol.getEnum(), port.getValuei());
            super.buildOutputs();
            logStatus();
            // LOG.info("sigh, buildOutputs2 {} {}", protocol.getEnum(), port.getValuei());
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
            // LOG.info("sigh, buildSegment1 {} {}", protocol.getEnum(), port.getValuei());
            var segFault = super.buildSegment();
            // LOG.info("sigh, buildSegment2 {} {}", protocol.getEnum(), port.getValuei());
            return segFault;
        }

        @Override
        protected void beforeRegenerate() {
            // LOG.info("sigh, beforeRegen {} {}", protocol.getEnum(), port.getValuei());
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
