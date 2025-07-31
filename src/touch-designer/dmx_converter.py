# Script CHOP callback for converting pixels to DMX
# This goes in the pixels_to_dmx_stream_callbacks DAT

def onCook(scriptOp):
    """Convert 420x24 pixel data to linear DMX channels"""
    
    # Clear existing channels
    scriptOp.clear()
    
    # Get input CHOP (video_to_chop)
    if scriptOp.inputs:
        input_chop = scriptOp.inputs[0]
        
        # video_to_chop gives us 96 channels (24 rows × RGBA) × 420 samples (width)
        # We need to convert this to linear RGB data for DMX
        
        # Total DMX channels needed: 420 × 24 × 3 = 30,240
        total_dmx_channels = 30240
        
        # Create output with 1 sample per DMX channel
        scriptOp.numSamples = total_dmx_channels
        scriptOp.numChans = 1
        scriptOp.appendChan('dmx')
        
        # Fill DMX data by reading pixels in order
        dmx_index = 0
        
        # Process each row (24 rows)
        for row in range(24):
            # Process each pixel in row (420 pixels)
            for col in range(420):
                # Get RGBA channels for this pixel
                # Channels are named r0, g0, b0, a0, r1, g1, b1, a1, etc.
                r_chan_index = row * 4  # Each row has RGBA
                g_chan_index = row * 4 + 1
                b_chan_index = row * 4 + 2
                # Skip alpha (row * 4 + 3)
                
                # Get pixel values at column position
                if (r_chan_index < input_chop.numChans and 
                    col < input_chop.numSamples):
                    
                    # Get RGB values (0-1 range)
                    r = input_chop[r_chan_index][col].eval()
                    g = input_chop[g_chan_index][col].eval()
                    b = input_chop[b_chan_index][col].eval()
                    
                    # Convert to DMX values (0-255)
                    scriptOp[0][dmx_index] = int(r * 255)
                    scriptOp[0][dmx_index + 1] = int(g * 255)
                    scriptOp[0][dmx_index + 2] = int(b * 255)
                    
                    dmx_index += 3
    
    return