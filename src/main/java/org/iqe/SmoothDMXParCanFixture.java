package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.structure.StripFixture;
import org.springframework.test.util.ReflectionTestUtils;

/**
 * Smoothed DMX ParCan fixture with adjustable temporal smoothing
 * Reduces jumpy/strobe effects by interpolating between color changes
 */
public class SmoothDMXParCanFixture extends StripFixture {
    
    // Smoothing encoder instance (shared across all pixels in this fixture)
    private final SmoothParCanByteEncoder smoothEncoder;
    
    // Parameter to control smoothing amount
    public final CompoundParameter smoothing = 
        new CompoundParameter("Smoothing", 0.85, 0, 0.99)
        .setDescription("Temporal smoothing factor (0=none, 0.99=maximum)");
    
    public SmoothDMXParCanFixture(LX lx) {
        super(lx);
        
        // Create encoder with default smoothing
        this.smoothEncoder = new SmoothParCanByteEncoder(0.85f);
        
        // Add smoothing parameter to fixture
        addParameter(smoothing);
        
        // Listen for smoothing changes
        smoothing.addListener(p -> {
            smoothEncoder.setSmoothingFactor((float) smoothing.getValue());
            LOG.info("SmoothDMXParCanFixture smoothing updated to: {}", smoothing.getValue());
        });
        
        // Set protocol to ArtNet by default
        this.protocol.setValue(Protocol.ARTNET.ordinal());
        
        // Enable by default
        this.enabled.setValue(true);
        
        LOG.info("SmoothDMXParCanFixture created with smoothing: {}", smoothing.getValue());
    }
    
    @Override
    protected Segment buildSegment() {
        // Call parent to get normal segment, then use reflection to swap the encoder
        Segment segment = super.buildSegment();
        
        // Use reflection to replace the ByteEncoder with our smoothed version
        ReflectionTestUtils.setField(segment, "byteEncoder", smoothEncoder);
        
        // Log the segment details
        LOG.info("SmoothDMXParCanFixture buildSegment:");
        LOG.info("  Fixture points: {}", this.numPoints.getValuei());
        LOG.info("  ByteEncoder replaced with SmoothParCanByteEncoder");
        LOG.info("  Smoothing factor: {}", smoothing.getValue());
        
        return segment;
    }
    
    @Override
    protected void buildOutputs() {
        super.buildOutputs();
        
        LOG.info("SmoothDMXParCanFixture configured:");
        LOG.info("  Universe: {}", this.artNetUniverse.getValuei());
        LOG.info("  DMX Start: {}", this.dmxChannel.getValuei());
        LOG.info("  Pixels: {}", this.numPoints.getValuei());
        LOG.info("  Smoothing: {}", smoothing.getValue());
        LOG.info("  IP: {}", this.host.getString());
    }
}