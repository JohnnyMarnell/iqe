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
import heronarts.lx.modulator.LXModulator;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.LXParameter.Units;
import heronarts.lx.parameter.TriggerParameter;
import heronarts.lx.pattern.LXPattern;
import heronarts.lx.utils.LXUtils;
import jkbstudio.autopilot.Autopilot;
import java.util.Timer;
import java.util.TimerTask;

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
      new TriggerParameter("PattTrx")
      .setDescription("Transition all active patterns to their next pattern");
  
  public final TriggerParameter transitionPalette =
      new TriggerParameter("PalTrx")
      .setDescription("Transition to next color palette");
  
  public final TriggerParameter pauseTransitions =
      new TriggerParameter("Pause30s")
      .setDescription("Pause all transitions for 30 seconds");

  public final CompoundParameter maxTransitionMs =
      new CompoundParameter("MaxTrxMs", 500, 100, 15000)
      .setDescription("Maximum transition time in milliseconds")
      .setUnits(Units.MILLISECONDS);
  
  private Timer pauseTimer = null;
  private boolean transitionsPaused = false;
  private long pauseEndTime = 0;
  private LXModulator dumbPixelBlazeHackLFO = null;
  private boolean dumbPixelBlazeHackLFOWasRunning = false;

  public AutopilotIQE(LX lx) {
    super(lx);

    // Add our parameters and make them visible in UI
    addVisibleParameter("audio", this.audio);
    addVisibleParameter("audioPercent", this.percentAudioReactive);
    addVisibleParameter("transitionAll", this.transitionAll);
    addVisibleParameter("transitionPalette", this.transitionPalette);
    addVisibleParameter("pauseTransitions", this.pauseTransitions);
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
    
    // Add listener to pause transitions for 30 seconds
    this.pauseTransitions.addListener(p -> {
      if (this.pauseTransitions.getValueb()) {
        pauseTransitionsFor30Seconds();
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
    // Use OSC commands for each channel to be consistent and avoid double triggering
    this.lx.engine.mixer.getChannels().forEach(channel -> {
      if (channel instanceof LXChannel) {
        LXChannel lxChannel = (LXChannel) channel;
        // Only transition if channel is enabled/active
        if (lxChannel.enabled.getValueb()) {
          int channelIndex = lxChannel.getIndex() + 1; // OSC uses 1-based indexing
          Audio.get().osc.command("/lx/mixer/channel/" + channelIndex + "/triggerPatternCycle");
          LX.log("Transitioned channel '" + lxChannel.getLabel() + "' to next pattern via OSC");
        }
      }
    });
  }

  @Override
  protected void enableTransitions(LXChannel channel) {
    // Skip if transitions are paused
    if (transitionsPaused) {
      return;
    }
    
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
    // Use only OSC command to avoid double triggering
    Audio.get().osc.command("/lx/palette/triggerSwatchCycle");
    LX.log("Triggered palette transition via OSC");
  }
  
  private LXModulator findDumbPixelBlazeHackLFO() {
    // Search through global modulators for the one with matching label
    for (LXModulator modulator : this.lx.engine.modulation.modulators) {
      if ("DumbPixelBlazeHackLFO".equals(modulator.label.getString())) {
        return modulator;
      }
    }
    return null;
  }
  
  private void pauseTransitionsFor30Seconds() {
    // Calculate new end time (add 30 seconds to existing or current time)
    long currentTime = System.currentTimeMillis();
    if (pauseEndTime > currentTime) {
      // Timer is already running, add 30 seconds to existing end time
      pauseEndTime += 30000;
      long totalSeconds = (pauseEndTime - currentTime) / 1000;
      LX.log("Extended pause by 30 seconds, total pause time: " + totalSeconds + " seconds");
    } else {
      // First press or timer expired, set new end time
      pauseEndTime = currentTime + 30000;
      LX.log("Paused all transitions for 30 seconds");
      
      // Only disable transitions on first press
      if (!transitionsPaused) {
        // Disable all channel transitions immediately
        this.lx.engine.mixer.getChannels().forEach(channel -> {
          if (channel instanceof LXChannel) {
            LXChannel lxChannel = (LXChannel) channel;
            lxChannel.transitionEnabled.setValue(false);
            lxChannel.autoCycleEnabled.setValue(false);
          }
        });
        
        // Also disable palette transitions
        LXPalette palette = this.lx.engine.palette;
        palette.transitionEnabled.setValue(false);
        palette.autoCycleEnabled.setValue(false);
        
        // Find and pause the DumbPixelBlazeHackLFO if it exists
        if (dumbPixelBlazeHackLFO == null) {
          dumbPixelBlazeHackLFO = findDumbPixelBlazeHackLFO();
        }
        if (dumbPixelBlazeHackLFO != null) {
          dumbPixelBlazeHackLFOWasRunning = dumbPixelBlazeHackLFO.running.isOn();
          if (dumbPixelBlazeHackLFOWasRunning) {
            dumbPixelBlazeHackLFO.running.setValue(false);
            LX.log("Paused DumbPixelBlazeHackLFO modulator");
          }
        } else {
          LX.log("DumbPixelBlazeHackLFO modulator not found");
        }
        
        transitionsPaused = true;
      }
    }
    
    // Cancel existing timer if any
    if (pauseTimer != null) {
      pauseTimer.cancel();
    }
    
    // Schedule new timer for the updated end time
    pauseTimer = new Timer();
    long delay = pauseEndTime - currentTime;
    pauseTimer.schedule(new TimerTask() {
      @Override
      public void run() {
        resumeTransitions();
      }
    }, delay);
  }
  
  private void resumeTransitions() {
    transitionsPaused = false;
    pauseEndTime = 0;  // Reset the end time
    
    // Re-enable channel transitions
    this.lx.engine.mixer.getChannels().forEach(channel -> {
      if (channel instanceof LXChannel) {
        enableTransitions((LXChannel) channel);
      }
    });
    
    // Re-enable palette transitions
    LXPalette palette = this.lx.engine.palette;
    palette.transitionEnabled.setValue(true);
    palette.autoCycleEnabled.setValue(true);
    
    // Resume the DumbPixelBlazeHackLFO if it was running before
    if (dumbPixelBlazeHackLFO != null && dumbPixelBlazeHackLFOWasRunning) {
      dumbPixelBlazeHackLFO.running.setValue(true);
      LX.log("Resumed DumbPixelBlazeHackLFO modulator");
    }
    
    LX.log("Resumed all transitions after pause expired");
    
    // Clean up timer
    if (pauseTimer != null) {
      pauseTimer.cancel();
      pauseTimer = null;
    }
  }

}
