package titanicsend.pattern.pixelblaze;

import heronarts.lx.LX;
import heronarts.lx.LXCategory;

@LXCategory("PixelBlaze")
public class PBXorcery extends PixelblazePattern {

	public PBXorcery(LX lx) {
		super(lx);
	}

	@Override
	protected String getScriptName() {
		return "xorcery";
	}
}
