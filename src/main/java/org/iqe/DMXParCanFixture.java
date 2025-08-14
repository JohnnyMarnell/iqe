package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.structure.StripFixture;
import org.springframework.test.util.ReflectionTestUtils;

/**
 * Simple DMX ParCan fixture that overrides buildSegment to use custom encoder
 * Each pixel outputs 7 DMX channels with dimmer always at 255
 */
public class DMXParCanFixture extends StripFixture {
    
    // Custom encoder for 7-channel ParCans
    private static final ParCanByteEncoder PARCAN_ENCODER = new ParCanByteEncoder();
    
    public DMXParCanFixture(LX lx) {
        super(lx);
        
        // Default configuration - can be overridden in JSON
//        this.numPoints.setValue(2);
//        this.spacing.setValue(10.0);
        
        // Set protocol to ArtNet by default
        this.protocol.setValue(Protocol.ARTNET.ordinal());
        
        // Don't hardcode IP - let it be set from JSON or UI
        // this.host.setValue("10.10.42.68");
        
        // Default to universe 1 (can be overridden in JSON)
//        this.artNetUniverse.setValue(1);
        
        // Start at DMX channel 1 (0-indexed)
        // Note: dmxChannel is in DMX channel units (1-based in UI, 0-based internally)
        // So dmxChannel=0 means DMX channel 1, dmxChannel=7 means DMX channel 8
//        this.dmxChannel.setValue(0);
        
        // Enable by default
        this.enabled.setValue(true);
    }
    
    @Override
    protected Segment buildSegment() {
        // Call parent to get normal segment, then use reflection to swap the encoder
        Segment segment = super.buildSegment();
        
        // Use reflection to replace the ByteEncoder
        ReflectionTestUtils.setField(segment, "byteEncoder", PARCAN_ENCODER);
        
        // Log the segment details
        LOG.info("DMXParCanFixture buildSegment:");
        LOG.info("  Fixture points: {}", this.numPoints.getValuei());
        LOG.info("  ByteEncoder replaced with ParCanByteEncoder (7 bytes/pixel)");
        
        return segment;
    }
    
    @Override
    protected void buildOutputs() {
        super.buildOutputs();
        
        LOG.info("DMXParCanFixture configured:");
        LOG.info("  Universe: {}", this.artNetUniverse.getValuei());
        LOG.info("  DMX Start: {}", this.dmxChannel.getValuei());
        LOG.info("  Pixels: {}", this.numPoints.getValuei());
        LOG.info("  Channels per pixel: 7 (Dimmer always 255)");
        LOG.info("  IP: {}", this.host.getString());
        LOG.info("  Total DMX channels used: {}", this.numPoints.getValuei() * 7);
        
        // Debug: Check what outputs were created
        this.outputDefinitions.forEach(outputDef -> {
            LOG.info("  Output created - Universe: {}, Channel: {}", 
                LXUtils.field(outputDef, "universe"),
                LXUtils.field(outputDef, "channel"));
            
            // Check the segments
            Object[] segments = (Object[]) LXUtils.field(outputDef, "segments");
            if (segments != null) {
                for (Object seg : segments) {
                    LOG.info("    Segment - startChannel: {}, numChannels: {}", 
                        "not_a_field_Claude",
                        LXUtils.field(seg, "numChannels"));
                }
            }
        });
    }
}