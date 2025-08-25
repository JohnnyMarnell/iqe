package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.model.LXPoint;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.structure.StripFixture;
import org.springframework.test.util.ReflectionTestUtils;

/**
 * DMX ParCan fixture that uses spatial averaging of nearby pixels
 * to create smoother, more coherent lighting effects.
 * Instead of temporal smoothing, this averages colors from surrounding pixels.
 */
public class SpatialAveragingParCanFixture extends StripFixture {
    
    // Spatial averaging encoder instance (unique per fixture)
    private final SpatialAveragingByteEncoder spatialEncoder;
    
    // Parameter to control the radius of pixels to sample (as percentage of total pixels)
    public final CompoundParameter samplingRadius = 
        new CompoundParameter("SampleRadius", 0.05, 0.01, 0.20)
        .setDescription("Percentage of nearby pixels to average (1%=tight, 20%=broad)");
    
    // Parameter to control the influence of brightness in averaging
    public final CompoundParameter brightnessWeight = 
        new CompoundParameter("BrightWeight", 1.0, 0.0, 2.0)
        .setDescription("How much brighter pixels influence the average (0=equal weight, 2=strong bias)")
        .setExponent(2.0);
    
    public SpatialAveragingParCanFixture(LX lx) {
        super(lx);
        
        // Sync with global sampling radius if it exists
        double initialRadius = GlobalControls.parcanSpatialRadius != null ? 
            GlobalControls.parcanSpatialRadius.getValue() : 0.05;
        
        // Create encoder with reference to LX for accessing all model points
        this.spatialEncoder = new SpatialAveragingByteEncoder(lx, (float) initialRadius);
        
        // Add parameters to fixture
        addParameter(samplingRadius);
        addParameter(brightnessWeight);
        
        // Set initial value from global
        samplingRadius.setValue(initialRadius);
        
        // Listen for radius changes
        samplingRadius.addListener(p -> {
            // Get fixture points from the model
            LXPoint[] points = new LXPoint[this.numPoints.getValuei()];
            for (int i = 0; i < points.length; i++) {
                if (i < this.points.size()) {
                    points[i] = this.points.get(i);
                }
            }
            spatialEncoder.setSamplingRadius((float) samplingRadius.getValue(), points);
            LOG.info("SpatialAveragingParCanFixture radius updated to: {}%", samplingRadius.getValue() * 100);
        });
        
        // Also listen to global parameter if it exists
        if (GlobalControls.parcanSpatialRadius != null) {
            GlobalControls.parcanSpatialRadius.addListener(p -> {
                samplingRadius.setValue(GlobalControls.parcanSpatialRadius.getValue());
            });
        }
        
        // Set protocol to ArtNet by default
        this.protocol.setValue(Protocol.ARTNET.ordinal());
        
        // Enable by default
        this.enabled.setValue(true);
        
        LOG.info("SpatialAveragingParCanFixture created with sampling radius: {}%", samplingRadius.getValue() * 100);
    }
    
    @Override
    protected Segment buildSegment() {
        // Call parent to get normal segment, then use reflection to swap the encoder
        Segment segment = super.buildSegment();
        
        // Get the fixture points for neighbor computation
        LXPoint[] points = new LXPoint[this.numPoints.getValuei()];
        for (int i = 0; i < points.length; i++) {
            if (i < this.points.size()) {
                points[i] = this.points.get(i);
            }
        }
        
        // Precompute neighbors based on current model
        spatialEncoder.precomputeNeighbors(points);
        
        // Use reflection to replace the ByteEncoder with our spatial version
        ReflectionTestUtils.setField(segment, "byteEncoder", spatialEncoder);
        
        // Log the segment details
        LOG.info("SpatialAveragingParCanFixture buildSegment:");
        LOG.info("  Fixture points: {}", this.numPoints.getValuei());
        LOG.info("  ByteEncoder replaced with SpatialAveragingByteEncoder");
        LOG.info("  Sampling radius: {}%", samplingRadius.getValue() * 100);
        LOG.info("  Total model points available for averaging: {}", lx.getModel().points.length);
        
        return segment;
    }
    
    @Override
    protected void buildOutputs() {
        super.buildOutputs();
        
        LOG.info("SpatialAveragingParCanFixture configured:");
        LOG.info("  Universe: {}", this.artNetUniverse.getValuei());
        LOG.info("  DMX Start: {}", this.dmxChannel.getValuei());
        LOG.info("  Pixels: {}", this.numPoints.getValuei());
        LOG.info("  Sampling Radius: {}%", samplingRadius.getValue() * 100);
        LOG.info("  IP: {}", this.host.getString());
        LOG.info("  Model size for averaging: {} points", lx.getModel().points.length);
    }
}