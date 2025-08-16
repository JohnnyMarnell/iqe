package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.Tempo;
import heronarts.lx.blend.DissolveBlend;
import heronarts.lx.blend.LXBlend;
import heronarts.lx.color.LXPalette;
import heronarts.lx.mixer.LXChannel;
import heronarts.lx.mixer.LXChannel.AutoCycleMode;
import heronarts.lx.modulation.LXCompoundModulation;
import heronarts.lx.modulation.LXParameterModulation.ModulationException;
import heronarts.lx.modulator.LXVariablePeriodModulator.ClockMode;
import heronarts.lx.modulator.VariableLFO;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.LXParameter.Units;
import heronarts.lx.parameter.TriggerParameter;
import heronarts.lx.pattern.LXPattern;
import heronarts.lx.utils.LXUtils;
import jkbstudio.autopilot.Autopilot;

/**
 * A project-specific autopilot
 */
public class AutopilotIQE extends Autopilot {

  public final CompoundParameter audio =
      new CompoundParameter("Audio", 0, 0, .5)
      .setDescription("Level of audio reactivity in the IQE Autopilot");

  public final CompoundParameter percentAudioReactive =
      new CompoundParameter("%Audio", 15, 0, 100)
      .setDescription("Percentage of modulators that are audio reactive.  Must be set before first run of Autopilot.")
      .setUnits(Units.PERCENT);

  public final TriggerParameter transitionAll =
      new TriggerParameter("TransitionAll")
      .setDescription("Transition all active patterns to their next pattern");
  
  public final TriggerParameter transitionPalette =
      new TriggerParameter("TransitionPalette")
      .setDescription("Transition to next color palette");

  public final CompoundParameter maxTransitionMs =
      new CompoundParameter("MaxTransMs", 500, 100, 15000)
      .setDescription("Maximum transition time in milliseconds")
      .setUnits(Units.MILLISECONDS);

  public AutopilotIQE(LX lx) {
    super(lx);

    // Add our parameters and make them visible in UI
    addVisibleParameter("audio", this.audio);
    addVisibleParameter("audioPercent", this.percentAudioReactive);
    addVisibleParameter("transitionAll", this.transitionAll);
    addVisibleParameter("transitionPalette", this.transitionPalette);
    addVisibleParameter("maxTransitionMs", this.maxTransitionMs);

    // Add other class' parameters to UI for convenience
    setParameterVisible(this.lx.engine.speed);
    
    // Add listener to transition all patterns when triggered
    this.transitionAll.addListener(p -> {
      if (this.transitionAll.getValueb()) {
        transitionAllPatterns();
      }
    });
    
    // Add listener to transition palette when triggered
    this.transitionPalette.addListener(p -> {
      if (this.transitionPalette.getValueb()) {
        transitionPalette();
      }
    });
    
    // Auto-update transition times when max changes
    this.maxTransitionMs.addListener(p -> {
      if (this.enabled.isOn()) {  // Only update if autopilot is enabled
        updateAllTransitionTimes();
      }
    });
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
      modulator.label.setValue(modulator.getLabel() + "_AUDIO");

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

  private void transitionAllPatterns() {
    // Iterate through all channels and trigger next pattern for active ones
    this.lx.engine.mixer.getChannels().forEach(channel -> {
      if (channel instanceof LXChannel) {
        LXChannel lxChannel = (LXChannel) channel;
        // Only transition if channel is enabled/active
        if (lxChannel.enabled.getValueb()) {
          lxChannel.goNextPattern();
          LX.log("Transitioned channel '" + lxChannel.getLabel() + "' to next pattern");
        }
      }
    });
  }

  @Override
  protected void enableTransitions(LXChannel channel) {
    // Set to dissolve blend
    for (LXBlend blend : channel.transitionBlendMode.getObjects()) {
      if (blend instanceof DissolveBlend) {
        channel.transitionBlendMode.setValue(blend);
        break;
      }
    }

    // Only set transition time if it's not already enabled (first start)
    // Otherwise preserve the existing value from the saved project
    if (!channel.transitionEnabled.getValueb()) {
      // Use our configurable max transition time (converted from ms to seconds)
      double maxTransitionSecs = this.maxTransitionMs.getValue() / 1000.0;
      double minTransitionSecs = Math.min(0.1, maxTransitionSecs * 0.2); // Min is 20% of max or 100ms
      channel.transitionTimeSecs.setValue(LXUtils.random(minTransitionSecs, maxTransitionSecs));
    }
    channel.transitionEnabled.setValue(true);

    // Only set autocycle times if not already enabled
    if (!channel.autoCycleEnabled.getValueb()) {
      channel.autoCycleTimeSecs.setValue(LXUtils.random(30, 75));
      channel.autoCycleMode.setValue(AutoCycleMode.RANDOM);
    }
    channel.autoCycleEnabled.setValue(true);
  }
  
  private void updateAllTransitionTimes() {
    // Update all channel transition times to use current max setting
    double maxTransitionSecs = this.maxTransitionMs.getValue() / 1000.0;
    double minTransitionSecs = Math.min(0.1, maxTransitionSecs * 0.2);
    
    this.lx.engine.mixer.getChannels().forEach(channel -> {
      if (channel instanceof LXChannel) {
        LXChannel lxChannel = (LXChannel) channel;
        if (lxChannel.transitionEnabled.getValueb()) {
          lxChannel.transitionTimeSecs.setValue(LXUtils.random(minTransitionSecs, maxTransitionSecs));
          LX.log("Updated channel '" + lxChannel.getLabel() + "' transition time");
        }
      }
    });
  }
  
  private void transitionPalette() {
    // Trigger palette transition to next swatch
    this.lx.engine.palette.triggerSwatchCycle.bang();
    LX.log("Triggered palette transition");
  }

}
