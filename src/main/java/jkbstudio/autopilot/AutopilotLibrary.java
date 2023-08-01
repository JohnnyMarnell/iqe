/**
 * Copyright 2022- Justin Belcher, Mark C. Slee, Heron Arts LLC
 *
 * This file is part of the LX Studio software library. By using
 * LX, you agree to the terms of the LX Studio Software License
 * and Distribution Agreement, available at: http://lx.studio/license
 *
 * Please note that the LX license is not open-source. The license
 * allows for free, non-commercial use.
 *
 * HERON ARTS MAKES NO WARRANTY, EXPRESS, IMPLIED, STATUTORY, OR
 * OTHERWISE, AND SPECIFICALLY DISCLAIMS ANY WARRANTY OF
 * MERCHANTABILITY, NON-INFRINGEMENT, OR FITNESS FOR A PARTICULAR
 * PURPOSE, WITH RESPECT TO THE SOFTWARE.
 *
 * @author Justin K Belcher <justin@jkb.studio>
 */

package jkbstudio.autopilot;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import heronarts.lx.pattern.LXPattern;
import heronarts.lx.utils.LXUtils;

public class AutopilotLibrary {

  static public enum Scale {
    ABSOLUTE,
    NORMALIZED
  }

  /**
   * Describes how to automate a parameter
   */
  static public class AutoParameter {

    static public final double DEFAULT_MIN_PERIOD = 15;
    static public final double DEFAULT_MAX_PERIOD = 45;
    static public final double DEFAULT_RANGE = 1;

    /**
     * Specifies min/max values are absolute or normalized
     */
    public final Scale scale;

    /**
     * Path to the parameter.  Must match the value passed to addParameter(path, ...)
     */
    public final String path;

    /**
     * Minimum parameter value while modulated
     */
    public final double min;

    /**
     * Maximum parameter value while modulated
     */
    public final double max;

    /**
     * Range which is active between min & max.
     * By default the entire range will be active.
     * If active range is less than total, random placement will be applied.
     */
    public final double range;

    /**
     * Minimum modulation period in seconds
     */
    public final double minPeriodSec;

    /**
     * Maximum modulation period in seconds
     */
    public final double maxPeriodSec;

    public AutoParameter(String path, Scale scale, double min, double max) {
      this(path, scale, min, max, DEFAULT_MIN_PERIOD, DEFAULT_MAX_PERIOD, max - min);
    }
    public AutoParameter(String path, Scale scale, double min, double max, double range) {
      this(path, scale, min, max, DEFAULT_MIN_PERIOD, DEFAULT_MAX_PERIOD, range);
    }

    public AutoParameter(String path, Scale scale, double min, double max, double minPeriod, double maxPeriod) {
      this(path, scale, min, max, minPeriod, maxPeriod, max - min);
    }

    public AutoParameter(String path, Scale scale, double min, double max, double minPeriod, double maxPeriod, double range) {
      this.path = path;
      this.scale = scale;
      this.min = LXUtils.min(min, max);
      this.max = LXUtils.max(min, max);
      this.range = LXUtils.min(Math.abs(range), this.max-this.min);
      this.minPeriodSec = LXUtils.min(minPeriod, maxPeriod);
      this.maxPeriodSec = LXUtils.max(minPeriod, maxPeriod);
    }
  }

  /**
   * Describes how to automate a pattern
   */
  static public class AutoPattern {

    public final Class<? extends LXPattern> pattern;
    public final List<AutoParameter> parameters = new ArrayList<AutoParameter>();

    public AutoPattern(Class<? extends LXPattern> pattern) {
      this.pattern = pattern;
    }

    public AutoPattern addParameter(AutoParameter param) {
      this.parameters.add(param);
      return this;
    }
  }

  private final Map<Class<? extends LXPattern>, AutoPattern> patternLookup = new HashMap<Class<? extends LXPattern>, AutoPattern>();

  public AutopilotLibrary() {

  }

  public AutoPattern addPattern(Class<? extends LXPattern> pattern) {
    if (patternLookup.containsKey(pattern)) {
      throw new IllegalStateException("Cannot add same pattern class to the Autopilot Library twice: " + pattern);
    }
    AutoPattern entry = new AutoPattern(pattern);
    patternLookup.put(pattern, entry);
    return entry;
  }

  public AutoPattern getPattern(LXPattern pattern) {
    return patternLookup.get(pattern.getClass());
  }
}
