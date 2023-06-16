package org.iqe.pattern;

import heronarts.lx.LX;
import heronarts.lx.color.LXColor;
import heronarts.lx.model.LXModel;
import heronarts.lx.model.LXPoint;
import heronarts.lx.pattern.LXPattern;
import org.iqe.Audio;

import java.util.Deque;
import java.util.LinkedList;

import static org.iqe.Audio.bars;

public class PianoRollPattern extends LXPattern {
    public static class Note {
        int note;
        int velocity;
        long start;
        long end;

        public Note(int note, int velocity, long start) {
            this.note = note;
            this.velocity = velocity;
            this.start = start;
        }
    }
    private Deque<Note> notes = new LinkedList<>();

    public PianoRollPattern(LX lx) {
        super(lx);
        Audio.get().orchestrator.addCustomOscMidiListener(this::handleMidi);
    }

    @Override
    protected void run(double v) {
        for (LXPoint p : model.points) colors[p.index] = LXColor.CLEAR;

        long now = getLX().engine.nowMillis;
        double window = bars(4);

        // Draw notes that started in the past (still on [playing] or off [finished] and started within window)
        for (Note event : notes) {
            double startZ = event.end > 0 ? 1. - (now - event.end) / window : 1.;
            double endZ = 1. - (now - event.start) / window;

            double hue = 20. + (event.note % 25) / 25. * 360.;
            double brightness = 75. + (event.velocity / 127.) * 25.;
            LXModel child = model.children[event.note % model.children.length];
            for (LXPoint p : child.points) {
                if (p.zn <= startZ && p.zn >= endZ) {
                    colors[p.index] = LXColor.hsb(hue, 100., brightness);
                }
            }
        }

        // Any fully rendered played notes can be discarded
        while (!notes.isEmpty() && notes.peekLast().end > 0 && notes.peekLast().end < now - window)
            notes.removeLast();
    }

    void handleMidi(int[] bytes) {
        long now = getLX().engine.nowMillis;
        int type = bytes[0] & 0xF0;
        int note = bytes[1];
        int velocity = bytes[2];

        // note on
        if (type == 0x90) {
            notes.addFirst(new Note(note, velocity, now));
        }
        // note off
        else if (type == 0x80) {
            for (Note event : notes) {
                if (event.note == note && event.end <= 0) {
                    event.end = now;
                    break;
                }
            }
        }
    }
}
