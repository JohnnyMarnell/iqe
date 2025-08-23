package org.iqe.effect;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;
import heronarts.lx.color.LXColor;
import heronarts.lx.effect.LXEffect;
import heronarts.lx.parameter.CompoundParameter;

@LXCategory(LXCategory.COLOR)
public class MindshowEffect extends LXEffect {
    
    public final CompoundParameter speed = 
        new CompoundParameter("Speed", 0.5, 0, 1)
        .setDescription("Speed of the cyclic pulsing");
    
    public final CompoundParameter colorBlend = 
        new CompoundParameter("Color", 0, 0, 1)
        .setDescription("Color blend from dark blue through purple to intense red");
    
    public final CompoundParameter sensitivity = 
        new CompoundParameter("Sensitivity", 1.0, 0, 1)
        .setDescription("Sensitivity of the color effect (1.0 = full effect, 0 = no effect)");
    
    private double phase = 0;
    
    public MindshowEffect(LX lx) {
        super(lx);
        addParameter("speed", speed);
        addParameter("colorBlend", colorBlend);
        addParameter("sensitivity", sensitivity);
    }
    
    @Override
    protected void run(double deltaMs, double dampedAmount) {
        // Update phase regardless of colorBlend value so speed always works
        double speedValue = speed.getValue();
        if (speedValue > 0) {
            phase += deltaMs * speedValue * 0.001;
            phase = phase % (2 * Math.PI);
        }
        
        double blendValue = colorBlend.getValue();
        
        // Calculate pulse amount - will be used to modulate the effect strength
        double pulseAmount = (Math.sin(phase) + 1) * 0.5;
        
        // Use full color range from blue (240°) through purple/magenta to red (0°)
        // This gives us a full spectrum transition
        float baseHue = (float)(240 - blendValue * 240) / 360f;  // 240° to 0°
        float baseSaturation = 80 + (float)(blendValue * 20);  // 80 to 100
        float baseBrightness = 30 + (float)(blendValue * 70);  // 30 to 100
        
        // Pulse the effect strength itself, not just brightness
        // When speed is 0, pulseAmount stays at 0.5 (no pulsing)
        // When speed > 0, it oscillates between 0 and 1
        float pulsedStrength = speedValue > 0 ? (float)pulseAmount : 1.0f;
        
        // Apply the pulsed strength to the overall effect
        // Sensitivity scales the effect strength
        float sensitivityValue = (float)sensitivity.getValue();
        float effectStrength = (float)(blendValue * dampedAmount * pulsedStrength * sensitivityValue);
        
        // If effect strength is 0, skip processing
        if (effectStrength == 0) {
            return;
        }
        
        for (int i = 0; i < colors.length; i++) {
            int original = colors[i];
            
            float origHue = LXColor.h(original) / 360f;
            float origSat = LXColor.s(original);
            float origBright = LXColor.b(original);
            
            // Blend towards the target color based on effect strength
            float newHue = origHue * (1 - effectStrength) + baseHue * effectStrength;
            float newSat = origSat * (1 - effectStrength) + baseSaturation * effectStrength;
            float newBright = origBright * (1 - effectStrength * 0.5f) + baseBrightness * effectStrength * 0.5f;
            
            colors[i] = LXColor.hsb(newHue * 360, newSat, newBright);
        }
    }
}