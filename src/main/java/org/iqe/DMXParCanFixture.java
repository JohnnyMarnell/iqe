package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.structure.StripFixture;

/**
 * DMX ParCan fixture for ArtNet control
 * Single pixel fixture that maps to RGB channels of a 7-channel DMX ParCan
 * Channel 1: Dimmer (not used)
 * Channels 2-4: RGB
 */
public class DMXParCanFixture extends StripFixture {
    
    public DMXParCanFixture(LX lx) {
        super(lx);
        
        // Configure as single pixel
        this.numPoints.setValue(1);
        this.spacing.setValue(1.0);
        
        // Set protocol to ArtNet
        this.protocol.setValue(Protocol.ARTNET.ordinal());
        
        // Default to the Pknight controller IP
        this.host.setValue("10.10.42.68");
        
        // Default to universe 1 (but can be overridden in JSON)
        this.artNetUniverse.setValue(1);
        
        // Enable by default
        this.enabled.setValue(true);
    }
    
    @Override
    protected void buildOutputs() {
        super.buildOutputs();
        LOG.info("DMXParCan {} configured - Universe: {}, Channel: {}, IP: {}", 
                 this.getLabel(), 
                 this.artNetUniverse.getValuei(),
                 this.dmxChannel.getValuei(),
                 this.host.getString());
    }
}