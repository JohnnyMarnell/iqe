/**
 * Copyright 2022- Mark C. Slee, Heron Arts LLC
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
 * @author Mark C. Slee <mark@heronarts.com>
 */

package org.iqe.pattern.pixelblaze;

import java.io.File;

import heronarts.glx.ui.UIColor;
import heronarts.glx.ui.vg.VGraphics;
import heronarts.lx.LX;
import heronarts.lx.command.LXCommand;
import heronarts.lx.parameter.CompoundParameter;
import heronarts.lx.studio.LXStudio.UI;
import heronarts.lx.studio.ui.device.UIDevice;
import heronarts.lx.studio.ui.device.UIDeviceControls;
import heronarts.lx.utils.LXUtils;
import heronarts.glx.ui.UI2dContainer;
import heronarts.glx.ui.component.UIButton;
import heronarts.glx.ui.component.UILabel;
import heronarts.glx.ui.component.UISlider;
public class UIPixelblazePattern implements UIDeviceControls<PixelblazePatterns.PixelBlazeBlowser>  {


    private PixelblazePatterns.PixelBlazeBlowser pattern;
    private UIButton openButton;

    private UIDeviceControls.Default defaultRenderer = new UIDeviceControls.Default();

    @Override
    public void buildDeviceControls(UI ui, UIDevice uiDevice, PixelblazePatterns.PixelBlazeBlowser pattern) {
        defaultRenderer.buildDeviceControls(ui, uiDevice, pattern);

        this.pattern = pattern;

        final UILabel fileLabel = (UILabel)
                new UILabel(0, 0, 120, 18)
                        .setLabel(pattern.scriptName.getString())
                        .setBackgroundColor(UIColor.BLACK)
                        .setBorderRounding(4)
                        .setTextAlignment(VGraphics.Align.CENTER, VGraphics.Align.MIDDLE)
                        .setTextOffset(0, -1)
                        .addToContainer(uiDevice);

        pattern.scriptName.addListener(p -> {
            fileLabel.setLabel(pattern.scriptName.getString());
        });

        this.openButton = (UIButton) new UIButton(122, 0, 18, 18) {
            @Override
            public void onToggle(boolean on) {
                if (on) {
//                    ui.applet.selectInput(
//                            "Select a file to open:",
//                            "onOpen",
//                            ui.lx.getMediaFile(LX.Media.PIXELBLAZE, pattern.scriptName.getString(), true),
//                            UIPixelblazePattern.this
//                    );
                }
            }
        }
                .setIcon(ui.theme.iconOpen)
                .setMomentary(true)
                .setDescription("Open Pixelblaze Script...")
                .addToContainer(uiDevice);

        final UIButton resetButton = (UIButton) new UIButton(140, 0, 18, 18)
                .setParameter(pattern.reset)
                .setIcon(ui.theme.iconLoop)
                .addToContainer(uiDevice);

        final UI2dContainer sliders = (UI2dContainer)
                UI2dContainer.newHorizontalContainer(uiDevice.getContentHeight() - 20, 2)
//                        .setPosition(0, 20)
                        .setPosition(50, 20)
                        .addToContainer(uiDevice);

        final UILabel error = (UILabel)
                new UILabel(0, 20, uiDevice.getContentWidth(), uiDevice.getContentHeight() - 20)
                        .setBreakLines(true)
                        .setTextAlignment(VGraphics.Align.LEFT, VGraphics.Align.TOP)
                        .addToContainer(uiDevice)
                        .setVisible(false);

        // Add sliders to container on every reload
        pattern.onReload.addListener(p -> {
            sliders.removeAllChildren();
            for (CompoundParameter slider : pattern.getSliders()) {
                new UISlider(UISlider.Direction.VERTICAL, 40, sliders.getContentHeight() - 14, slider)
                        .addToContainer(sliders);
            }
//            float contentWidth = LXUtils.maxf(140, sliders.getContentWidth());
            float contentWidth = LXUtils.maxf(200, sliders.getContentWidth());
            uiDevice.setContentWidth(contentWidth);
            resetButton.setX(contentWidth - resetButton.getWidth());
            this.openButton.setX(resetButton.getX() - 2 - this.openButton.getWidth());
            error.setWidth(contentWidth);
            fileLabel.setWidth(this.openButton.getX() - 2);
        }, true);

        pattern.error.addListener(p -> {
            String str = pattern.error.getString();
            boolean hasError = (str != null && !str.isEmpty());
            error.setLabel(hasError ? str : "");
            error.setVisible(hasError);
            sliders.setVisible(!hasError);
        }, true);

    }

    public void onOpen(final File openFile) {
        this.openButton.setActive(false);
        if (openFile != null) {
            LX lx = this.pattern.getLX();
//            lx.engine.addTask(() -> {
//                lx.command.perform(new LXCommand.Parameter.SetString(
//                        this.pattern.scriptName,
//                        lx.getMediaPath(LX.Media.PIXELBLAZE, openFile)
//                ));
//            });
        }
    }

}
