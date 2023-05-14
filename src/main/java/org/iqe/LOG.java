package org.iqe;

import heronarts.lx.LX;

/**
 * Kenny LOGgins. Poor man's sl4j
 */
public class LOG {
    private static boolean info = true;
    private static boolean debug = false;

    private static int loop = 0;
    private static int msg = 0;
    private static long lastTickMs = -1;

    public static void info(String msg, Object ... args) {
        if (!info) return;
        out("INFO", format(msg, args));
    }

    public static void debug(String msg, Object ... args) {
        if (!debug) return;
        out("DEBUG", format(msg, args));
    }

    // Don't worry, it's already slow
    private static String format(String msg, Object ... args) {
        return msg.replaceAll("\\{}", "%s").formatted(args);
    }

    private static void out(String level, String text) {
        long now = Audio.get() == null ? System.currentTimeMillis() : Audio.now();
        if (now != lastTickMs) {
            lastTickMs = now;
            ++loop;
            msg = 1;
            System.out.printf("%4d %2d %s %s%n", loop, msg, "DEBUG", "New tick");
        }
        ++msg;
        System.out.printf("%4d %2d %s %s%n", loop, msg, level, text);
    }
}
