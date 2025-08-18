package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.Tempo;
import heronarts.lx.blend.DissolveBlend;
import heronarts.lx.blend.LXBlend;
import heronarts.lx.color.LXPalette;
import heronarts.lx.mixer.LXAbstractChannel;
import heronarts.lx.mixer.LXChannel;
import heronarts.lx.mixer.LXGroup;
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
import java.util.HashMap;
import java.util.Map;

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

  // These are now in GlobalControls

  public final CompoundParameter maxTransitionMs =
      new CompoundParameter("trxMx", 500, 100, 15000)
      .setDescription("Maximum transition time in milliseconds")
      .setUnits(Units.MILLISECONDS);
  
  // Channel solo parameters
  public final CompoundParameter soloChannel = 
      new CompoundParameter("soloCh", 0, 0, 10)
      .setDescription("Solo channel selector (0=None, 1-N=Channel)");
  
  public final TriggerParameter clearSolo =
      new TriggerParameter("clearSolo")
      .setDescription("Clear solo and restore all channels");
  
  public final CompoundParameter soloAutoRestoreTime =
      new CompoundParameter("soloTime", 0, 0, 30)
      .setDescription("Auto-restore time in seconds (0 = disabled)")
      .setUnits(Units.SECONDS);
  
  private Timer pauseTimer = null;
  private boolean transitionsPaused = false;
  private long pauseEndTime = 0;
  private LXModulator dumbPixelBlazeHackLFO = null;
  private boolean dumbPixelBlazeHackLFOWasRunning = false;
  
  // Channel solo state tracking
  private Timer soloTimer = null;
  private long soloEndTime = 0;
  private Map<LXAbstractChannel, Boolean> savedChannelStates = new HashMap<>();
  private Map<LXAbstractChannel, Double> savedFaderPositions = new HashMap<>();
  private int currentSoloChannel = 0; // 0 means no solo

  public AutopilotIQE(LX lx) {
    super(lx);

    // Add our parameters and make them visible in UI
    addVisibleParameter("audio", this.audio);
    addVisibleParameter("audioPercent", this.percentAudioReactive);
    // transitionAll, pauseTransitions, and transitionPalette are now in GlobalControls
    addVisibleParameter("maxTransitionMs", this.maxTransitionMs);
    addVisibleParameter("soloChannel", this.soloChannel);
    addVisibleParameter("soloAutoRestoreTime", this.soloAutoRestoreTime);
    addVisibleParameter("clearSolo", this.clearSolo);

    // Add other class' parameters to UI for convenience
    setParameterVisible(this.lx.engine.speed);
    
    // Add listener to transition all patterns when triggered (now from GlobalControls)
    GlobalControls.transitionAll.addListener(p -> {
      if (GlobalControls.transitionAll.getValueb()) {
        transitionAllPatterns();
      }
    });
    
    // Add listener to transition palette when triggered (now from GlobalControls)
    GlobalControls.transitionPalette.addListener(p -> {
      if (GlobalControls.transitionPalette.getValueb()) {
        transitionPalette();
      }
    });
    
    // Add listener to pause transitions for 30 seconds (now from GlobalControls)
    GlobalControls.pauseTransitions.addListener(p -> {
      if (GlobalControls.pauseTransitions.getValueb()) {
        pauseTransitionsFor30Seconds();
      }
    });
    
    // Auto-update transition times when max changes
    this.maxTransitionMs.addListener(p -> {
      if (this.enabled.isOn()) {  // Only update if autopilot is enabled
        updateAllTransitionTimes();
      }
    });
    
    // Add listener for solo channel changes
    this.soloChannel.addListener(p -> {
      // Round to nearest integer for channel selection
      int selectedChannel = Math.round((float)this.soloChannel.getValue());
      if (selectedChannel != currentSoloChannel) {
        if (selectedChannel == 0) {
          // Clear solo
          clearChannelSolo();
        } else {
          // Solo the selected channel
          soloChannelByIndex(selectedChannel - 1); // Convert to 0-based index
        }
      }
    });
    
    // Add listener for clear solo button
    this.clearSolo.addListener(p -> {
      if (this.clearSolo.getValueb()) {
        this.soloChannel.setValue(0); // This will trigger the soloChannel listener
      }
    });
    
    // Register OSC listener for solo control
    registerOscSoloControl();
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
  
  private void registerOscSoloControl() {
    // Register custom OSC paths for solo control
    Audio.get().osc.on("/lx/autopilot/solo", msg -> {
      // Accept either int or float values
      float value;
      try {
        value = msg.getFloat(0);
      } catch (Exception e) {
        // Try as int if float fails
        try {
          value = (float) msg.getInt(0);
        } catch (Exception e2) {
          LX.log("Invalid OSC solo value");
          return;
        }
      }
      
      if (value >= 0 && value <= this.soloChannel.getRange()) {
        this.soloChannel.setValue(value);
        LX.log("OSC solo channel set to: " + value);
      }
    });
    
    Audio.get().osc.on("/lx/autopilot/solo/clear", msg -> {
      this.clearSolo.bang();
      LX.log("OSC solo cleared");
    });
  }
  
  private void soloChannelByIndex(int channelIndex) {
    // Save current states if not already soloing
    if (currentSoloChannel == 0) {
      saveChannelStates();
    }
    
    // Find the target channel and determine what needs to be enabled
    LXAbstractChannel targetChannel = null;
    LXGroup parentGroup = null;
    int index = 0;
    
    // First pass: find the target channel
    for (LXAbstractChannel abstractChannel : this.lx.engine.mixer.getChannels()) {
      if (abstractChannel instanceof LXChannel || abstractChannel instanceof LXGroup) {
        if (index == channelIndex) {
          targetChannel = abstractChannel;
          // If it's a regular channel, check if it has a parent group
          if (targetChannel instanceof LXChannel) {
            LXChannel ch = (LXChannel) targetChannel;
            // Check if this channel belongs to a group
            // Try to get the group using getGroup() method
            try {
              LXGroup group = ch.getGroup();
              if (group != null) {
                parentGroup = group;
              }
            } catch (Exception e) {
              // Method might not exist in this version
            }
          }
          break;
        }
        index++;
      }
    }
    
    if (targetChannel == null) {
      LX.log("Channel index " + channelIndex + " not found");
      return;
    }
    
    // Second pass: enable/disable channels based on solo logic
    for (LXAbstractChannel abstractChannel : this.lx.engine.mixer.getChannels()) {
      if (abstractChannel instanceof LXChannel || abstractChannel instanceof LXGroup) {
        boolean shouldEnable = false;
        
        if (abstractChannel == targetChannel) {
          // This is the selected channel
          shouldEnable = true;
        } else if (targetChannel instanceof LXGroup && abstractChannel instanceof LXChannel) {
          // Target is a group, check if this channel is a child of it
          LXChannel ch = (LXChannel) abstractChannel;
          try {
            LXGroup group = ch.getGroup();
            if (group == targetChannel) {
              shouldEnable = true;
            }
          } catch (Exception e) {
            // Method might not exist
          }
        } else if (parentGroup != null && abstractChannel == parentGroup) {
          // Target has a parent group, enable the parent too
          shouldEnable = true;
        }
        
        abstractChannel.enabled.setValue(shouldEnable);
        
        if (shouldEnable) {
          // Set fader to full for soloed channels
          abstractChannel.fader.setValue(1.0);
          LX.log("Solo enabled for: " + abstractChannel.getLabel() + " (fader set to 100%)");
        }
      }
    }
    
    currentSoloChannel = channelIndex + 1; // Store as 1-based
    
    // Start auto-restore timer if configured
    double restoreTime = this.soloAutoRestoreTime.getValue();
    if (restoreTime > 0) {
      startSoloRestoreTimer(restoreTime);
      LX.log("Solo will auto-clear in " + restoreTime + " seconds");
    } else {
      LX.log("Solo activated (no auto-restore timer)");
    }
  }
  
  private void saveChannelStates() {
    // Save the current enabled state and fader position of each channel and group
    savedChannelStates.clear();
    savedFaderPositions.clear();
    for (LXAbstractChannel abstractChannel : this.lx.engine.mixer.getChannels()) {
      if (abstractChannel instanceof LXChannel || abstractChannel instanceof LXGroup) {
        savedChannelStates.put(abstractChannel, abstractChannel.enabled.getValueb());
        savedFaderPositions.put(abstractChannel, abstractChannel.fader.getValue());
      }
    }
    LX.log("Saved states and fader positions for " + savedChannelStates.size() + " channels/groups");
  }
  
  private void clearChannelSolo() {
    if (currentSoloChannel == 0) {
      return; // Nothing to clear
    }
    
    // Restore saved channel states and fader positions
    for (Map.Entry<LXAbstractChannel, Boolean> entry : savedChannelStates.entrySet()) {
      LXAbstractChannel channel = entry.getKey();
      // Restore enabled state
      channel.enabled.setValue(entry.getValue());
      // Restore fader position
      Double savedFaderValue = savedFaderPositions.get(channel);
      if (savedFaderValue != null) {
        channel.fader.setValue(savedFaderValue);
      }
    }
    
    currentSoloChannel = 0;
    soloEndTime = 0;
    
    // Cancel any active timer
    if (soloTimer != null) {
      soloTimer.cancel();
      soloTimer = null;
    }
    
    LX.log("Solo cleared, restored " + savedChannelStates.size() + " channel/group states and fader positions");
    savedChannelStates.clear();
    savedFaderPositions.clear();
  }
  
  private void startSoloRestoreTimer(double seconds) {
    // Cancel existing timer if any
    if (soloTimer != null) {
      soloTimer.cancel();
    }
    
    Object[] result = startOrExtendTimer(
      soloEndTime,
      seconds,
      "solo auto-restore timer",
      null,  // No special first-start action needed
      () -> {
        soloChannel.setValue(0);  // Clear solo when timer expires
      }
    );
    
    soloEndTime = (long) result[0];
    soloTimer = (Timer) result[1];
  }
  
  /**
   * Generic timer extension helper that adds time to existing timer or starts new one
   * @param currentEndTime Current end time of the timer (0 if not running)
   * @param additionalSeconds Seconds to add
   * @param timerName Name for logging
   * @param onFirstStart Callback to run only when timer first starts (not on extension)
   * @param onExpire Callback to run when timer expires
   * @return Array with [newEndTime, newTimer]
   */
  private Object[] startOrExtendTimer(long currentEndTime, double additionalSeconds, String timerName,
                                      Runnable onFirstStart, Runnable onExpire) {
    long currentTime = System.currentTimeMillis();
    long additionalMs = (long)(additionalSeconds * 1000);
    long newEndTime;
    
    if (currentEndTime > currentTime) {
      // Timer already running, add to existing end time
      newEndTime = currentEndTime + additionalMs;
      long totalSeconds = (newEndTime - currentTime) / 1000;
      LX.log("Extended " + timerName + " by " + additionalSeconds + " seconds, total remaining: " + totalSeconds + " seconds");
    } else {
      // First start or timer expired
      newEndTime = currentTime + additionalMs;
      LX.log("Starting " + timerName + " for " + additionalSeconds + " seconds");
      
      // Run first-start callback if provided
      if (onFirstStart != null) {
        onFirstStart.run();
      }
    }
    
    // Create new timer scheduled for the end time
    Timer newTimer = new Timer();
    long delay = newEndTime - currentTime;
    newTimer.schedule(new TimerTask() {
      @Override
      public void run() {
        LX.log(timerName + " expired");
        if (onExpire != null) {
          onExpire.run();
        }
      }
    }, delay);
    
    return new Object[] { newEndTime, newTimer };
  }
  
  private void pauseTransitionsFor30Seconds() {
    // Cancel existing timer if any
    if (pauseTimer != null) {
      pauseTimer.cancel();
    }
    
    Object[] result = startOrExtendTimer(
      pauseEndTime, 
      30, 
      "pause timer",
      !transitionsPaused ? () -> {
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
      } : null,
      () -> resumeTransitions()
    );
    
    pauseEndTime = (long) result[0];
    pauseTimer = (Timer) result[1];
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
