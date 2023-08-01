package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.Tempo;
import heronarts.lx.color.LXPalette;
import heronarts.lx.color.LXPalette.AutoCycleMode;
import heronarts.lx.mixer.LXChannel;
import heronarts.lx.modulation.LXCompoundModulation;
import heronarts.lx.modulation.LXParameterModulation.ModulationException;
import heronarts.lx.modulator.LXVariablePeriodModulator.ClockMode;
import heronarts.lx.modulator.VariableLFO;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.LXParameter.Units;
import heronarts.lx.pattern.LXPattern;
import jkbstudio.autopilot.Autopilot;

/**
 * A project-specific autopilot
 */
public class AutopilotIQE extends Autopilot {

  public final CompoundParameter audio =
      new CompoundParameter("Audio", 0, 0, .5)
      .setDescription("Level of audio reactivity in the IQE Autopilot");

  public final CompoundParameter percentAudioReactive =
      new CompoundParameter("%Audio", 10, 0, 100)
      .setDescription("Percentage of modulators that are audio reactive.  Must be set before first run of Autopilot.")
      .setUnits(Units.PERCENT);

  public AutopilotIQE(LX lx) {
    super(lx);

    addUserParameter("audio", this.audio);
    addUserParameter("audioPercent", this.percentAudioReactive);
  }

  /**
   * Called every time after Autopilot is enabled
   */
  @Override
  protected void onDidEnable() {
    // For IQE let's be sure the color palette cycles!
    LXPalette palette = this.lx.engine.palette;
    if (!palette.transitionEnabled.isOn()) {
      palette.transitionTimeSecs.setValue(5);
      palette.transitionEnabled.setValue(true);
    }
    if (!palette.autoCycleEnabled.isOn()) {
      palette.autoCycleMode.setValue(AutoCycleMode.RANDOM);
      palette.autoCycleTimeSecs.setValue(35);
      palette.autoCycleEnabled.setValue(true);
    }
  }

  /**
   * Called for each modulator created by Autopilot
   */
  @Override
  protected void onModAdded(CompoundParameter parameter, VariableLFO modulator, LXCompoundModulation modulation) {

    // ** IQE audio/tempo reaction **
    // For a percentage of newly created modulators, sync them to the beat.
    // This percentage is controlled with the %Audio knob.  It needs to be set *prior* to the first autopilot run.

    if (Math.random() < this.percentAudioReactive.getNormalized()) {
      // Change modulator to tempo quarter beats
      modulator.tempoDivision.setValue(Tempo.Division.QUARTER);
      modulator.clockMode.setValue(ClockMode.SYNC);

      // Discard previous modulation amount
      double previousRange = modulation.range.getValue();
      modulation.range.setValue(0);

      // Map global Audio knob to modulation amount, now that this is possible
      try {
        LXCompoundModulation audioMod = new LXCompoundModulation(this.lx.engine.modulation, this.audio, modulation.range);
        audioMod.range.setValue(previousRange / 2);
        this.lx.engine.modulation.addModulation(audioMod);
      } catch (ModulationException e) {
        e.printStackTrace();
        LX.error(e, "Error adding audio modulation in IQE Autopilot");
      }
    }
  }

  @Override
  protected boolean checkChannelQualifies(LXChannel channel) {
    // Example: how to exclude the 'FX' channel from being modulated by Autopilot
    // if (channel.label.equals("FX")) {
    //   return false;
    // }
    return true;
  }

  @Override
  protected boolean checkPatternQualifies(LXChannel channel, LXPattern pattern) {
    return true;
  }

}
