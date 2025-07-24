/***
 * Patched original LXPattern, since onLoop() is final and we want to
 * be able to scale time delta.
 */
package heronarts.lx.pattern;

import javax.management.RuntimeMBeanException;

import com.google.gson.JsonObject;
import heronarts.lx.LX;
import heronarts.lx.LXComponent;
import heronarts.lx.LXDeviceComponent;
import heronarts.lx.LXTime;
import heronarts.lx.blend.LXBlend;
import heronarts.lx.mixer.LXChannel;
import heronarts.lx.mixer.LXMixerEngine;
import heronarts.lx.mixer.LXChannel.CompositeMode;
import heronarts.lx.osc.LXOscComponent;
import heronarts.lx.parameter.BooleanParameter;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.parameter.LXParameter;
import heronarts.lx.parameter.LXParameterListener;
import heronarts.lx.parameter.ObjectParameter;
import heronarts.lx.parameter.TriggerParameter;
import heronarts.lx.utils.LXUtils;
import org.iqe.Audio;
import org.iqe.GlobalControls;

public abstract class LXPattern extends LXDeviceComponent implements LXComponent.Renamable, LXOscComponent {
   static {
      System.out.println("*************** Using patched LXPattern ");
   }

   private int index = -1;
   private int intervalBegin = -1;
   private int intervalEnd = -1;
   private double compositeDampingLevel = 1.0;
   public final BooleanParameter enabled = (new BooleanParameter("Enabled", true)).setDescription("Whether the pattern is eligible for playlist cycling or compositing");
   public final TriggerParameter recall = (new TriggerParameter("Recall", () -> {
      this.getChannel().goPattern(this);
   })).setDescription("Recalls this pattern to become active on the channel");
   public final ObjectParameter<LXBlend> compositeMode = (new ObjectParameter("Composite Blend", new LXBlend[1])).setDescription("Specifies the blending function used for blending of patterns on the channel");
   private LXBlend activeCompositeBlend;
   public final CompoundParameter compositeLevel = (new CompoundParameter("Composite Level", 1.0)).setDescription("Alpha level to composite pattern at when in channel blend mode");
   private final LXParameterListener onEnabled = (p) -> {
      boolean isEnabled = this.enabled.isOn();
      LXChannel channel = this.getChannel();
      if (channel != null && channel.compositeMode.getEnum() == CompositeMode.BLEND) {
         if (isEnabled) {
            channel.onPatternEnabled(this);
         }

         if (!channel.compositeDampingEnabled.isOn()) {
            if (isEnabled) {
               this._activate();
            } else {
               this._deactivate();
            }
         }
      }

   };
   private final LXParameterListener onCompositeMode = (p) -> {
      this.activeCompositeBlend.onInactive();
      this.activeCompositeBlend = (LXBlend)this.compositeMode.getObject();
      this.activeCompositeBlend.onActive();
   };
   protected double runMs = 0.0;
   private boolean isActive = false;
   // TODO: Removed because of compiler error
   // public final Profiler profiler = new Profiler(this);

   protected LXPattern(LX lx) {
      super(lx);
      this.label.setDescription("The name of this pattern");
      this.addLegacyInternalParameter("autoCycleEligible", this.enabled);
      this.addParameter("enabled", this.enabled);
      this.addParameter("recall", this.recall);
      this.addParameter("compositeMode", this.compositeMode);
      this.addParameter("compositeLevel", this.compositeLevel);
      this.updateCompositeBlendOptions();
      this.compositeMode.addListener(this.onCompositeMode);
      this.enabled.addListener(this.onEnabled);
   }

   public boolean isHiddenControl(LXParameter parameter) {
      return parameter == this.recall || parameter == this.compositeMode || parameter == this.compositeLevel || parameter == this.enabled;
   }

   public String getPath() {
      return "pattern/" + (this.index + 1);
   }

   public void updateCompositeBlendOptions() {
      LXBlend[] var4;
      int var3 = (var4 = (LXBlend[])this.compositeMode.getObjects()).length;

      for(int var2 = 0; var2 < var3; ++var2) {
         LXBlend blend = var4[var2];
         if (blend != null) {
            blend.dispose();
         }
      }

      this.compositeMode.setObjects(this.lx.engine.mixer.instantiateChannelBlends());
      this.activeCompositeBlend = (LXBlend)this.compositeMode.getObject();
      this.activeCompositeBlend.onActive();
   }

   public void setIndex(int index) {
      this.index = index;
   }

   public int getIndex() {
      return this.index;
   }

   public final LXChannel getChannel() {
      return (LXChannel)this.getParent();
   }

   public final LXPattern setChannel(LXChannel channel) {
      this.setParent(channel);
      return this;
   }

   public LXPattern setInterval(int begin, int end) {
      this.intervalBegin = begin;
      this.intervalEnd = end;
      return this;
   }

   public LXPattern clearInterval() {
      this.intervalBegin = this.intervalEnd = -1;
      return this;
   }

   public final boolean hasInterval() {
      return this.intervalBegin >= 0 && this.intervalEnd >= 0;
   }

   public final boolean isInInterval() {
      if (!this.hasInterval()) {
         return false;
      } else {
         int now = LXTime.hour() * 60 + LXTime.minute();
         if (this.intervalBegin < this.intervalEnd) {
            return now >= this.intervalBegin && now < this.intervalEnd;
         } else {
            return now >= this.intervalBegin || now < this.intervalEnd;
         }
      }
   }

   public final LXPattern setAutoCycleEligible(boolean eligible) {
      this.enabled.setValue(eligible);
      return this;
   }

   public final LXPattern toggleAutoCycleEligible() {
      this.enabled.toggle();
      return this;
   }

   public final boolean isAutoCycleEligible() {
      return this.enabled.isOn() && (!this.hasInterval() || this.isInInterval());
   }

   public void initCompositeDamping(boolean wasActivePattern) {
      boolean isEnabled = this.enabled.isOn();
      this.compositeDampingLevel = (double)(isEnabled ? 1 : 0);
      if (isEnabled && !wasActivePattern) {
         this.onActive();
      } else if (!isEnabled && wasActivePattern) {
         this.onInactive();
      }

   }

   public void updateCompositeDamping(double deltaMs, boolean dampingOn, double dampingTimeSecs) {
      boolean isEnabled = this.enabled.isOn();
      if (!dampingOn) {
         this.compositeDampingLevel = (double)(isEnabled ? 1 : 0);
      } else if (isEnabled) {
         if (this.compositeDampingLevel < 1.0) {
            if (this.compositeDampingLevel == 0.0) {
               this.onActive();
            }

            this.compositeDampingLevel = LXUtils.min(1.0, this.compositeDampingLevel + deltaMs / (dampingTimeSecs * 1000.0));
         }
      } else if (this.compositeDampingLevel > 0.0) {
         this.compositeDampingLevel = LXUtils.max(0.0, this.compositeDampingLevel - deltaMs / (dampingTimeSecs * 1000.0));
         if (this.compositeDampingLevel == 0.0) {
            this.onInactive();
         }
      }

   }

   public double getCompositeDampingLevel() {
      return this.compositeDampingLevel;
   }

   protected final void onLoop(double deltaMs) {
      if (!this.isActive) {
         this.isActive = true;
         this.onActive();
      }

      long runStart = System.nanoTime();
      deltaMs *= 1.0 + GlobalControls.speed.getNormalized() * 20.0;
      this.runMs += deltaMs;
      this.run(deltaMs);
      
      // TODO: Removed because of compiler error
      // this.profiler.runNanos = System.nanoTime() - runStart;
   }

   protected abstract void run(double var1);

   public final void activate(LXMixerEngine.PatternFriendAccess lock) {
      if (lock == null) {
         throw new IllegalStateException("Only the LXMixerEngine may call LXPattern.activate()");
      } else {
         this._activate();
      }
   }

   private void _activate() {
   }

   public final void deactivate(LXMixerEngine.PatternFriendAccess lock) {
      if (lock == null) {
         throw new IllegalStateException("Only the LXMixerEngine may call LXPattern.activate()");
      } else {
         this._deactivate();
      }
   }

   private void _deactivate() {
      if (this.isActive) {
         this.isActive = false;
         this.onInactive();
      }

   }

   protected void onActive() {
   }

   protected void onInactive() {
   }

   public void onTransitionStart() {
   }

   public void onTransitionEnd() {
   }

   public void load(LX lx, JsonObject obj) {
      super.load(lx, obj);
      this.compositeDampingLevel = (double)(this.enabled.isOn() ? 1 : 0);
   }

   public void dispose() {
      this.enabled.removeListener(this.onEnabled);
      this.compositeMode.removeListener(this.onCompositeMode);
      super.dispose();
   }
}
