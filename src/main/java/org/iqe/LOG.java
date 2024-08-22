package org.iqe;

import heronarts.lx.LX;
import heronarts.lx.parameter.LXParameter;

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

    public static void error(String msg, Object ... args) {
        out("ERROR", format(msg, args));
    }

    // Don't worry, it's already slow
    public static String format(String msg, Object ... args) {
        for (int i = 0; i < args.length; i++) {
            Object o = args[i];
            if (o instanceof LXParameter) {
                o = ((LXParameter) o).getValue();
            }
            args[i] = o;
        }
        return msg.replaceAll("\\{}", "%s").formatted(args);
    }

    private static void out(String level, String text) {
        long now = Audio.get() == null ? System.currentTimeMillis() : Audio.now();
        if (now != lastTickMs) {
            lastTickMs = now;
            ++loop;
            msg = 0;
            debug("New tick");
        }
        ++msg;
        if ("ERROR".equals(level)) {
            System.out.printf("\033[1;31m %4d %2d %s %s \033[0m %n", loop, msg, level, text);
        } else {
            System.out.printf("%4d %2d %s %s%n", loop, msg, level, text);
        }
    }
}
