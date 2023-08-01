package heronarts.lx.studio;

import heronarts.lx.LX;
import java.io.File;
import java.io.IOException;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Calendar;

/**
 * TODO: Temporary measures in place until I get toolchain correctly setup
 *       Additionally, this helps with showing available CLI args and their code paths.
 */
public final class ChromatikIQE extends LXStudio {

    public static final String APP_NAME = "Chromatik";
    private static final String FLAG_HEADLESS = "--headless";
    private static final String FLAG_OPENGL = "--opengl";
    private static final String FLAG_WARNINGS = "--warnings";
    private static final String FLAG_INSTALL_EXAMPLES = "--install-examples";
    private static final String FLAG_DISABLE_ZEROCONF = "--disable-zeroconf";
    private static final String FLAG_DISABLE_PREFERENCES = "--disable-preferences";
    private static final String FLAG_ENABLE_PLUGIN = "--enable-plugin";
    private static final String FLAG_CLASSPATH_PLUGIN = "--classpath-plugin";
    private static final String FLAG_FORCE_OUTPUT = "--force-output";
    private static final String FLAG_REQUIRE_LICENSE = "--require-license";
    private static final DateFormat LOG_FILENAME_FORMAT = new SimpleDateFormat("'Chromatik-'yyyy.MM.dd-HH.mm.ss'.log'");
    private static final String CHROMATIK_PREFIX = "Chromatik";

    private ChromatikIQE(LXStudio.Flags flags) throws IOException {
        super(flags);
    }

    private static LX.Permissions createPermissions() {
        // TODO: A hack until I get toolchain correctly setup, and re-auth problems fixed
        if (1 == 1) return new LX.Permissions() {
            @Override
            public boolean canSave() {
                return true;
            }

            @Override
            public int getMaxPoints() {
                return Integer.MAX_VALUE;
            }

            @Override
            public boolean canRunPlugins() {
                return true;
            }

            @Override
            public boolean hasPackageLicense(String s) {
                return true;
            }
        };
        return new LX.Permissions() {
            public boolean canSave() {
                return License.get().canSave();
            }

            public int getMaxPoints() {
                return License.get().getMaxPoints();
            }

            public boolean canRunPlugins() {
                return License.get().canRunPlugins();
            }

            public boolean hasPackageLicense(String packageName) {
                return License.get().hasPackage(packageName);
            }
        };
    }

    protected final LX.Permissions getPermissions() {
        return createPermissions();
    }

    public void saveProject(File file) {
        if (this.permissions.canSave()) {
            super.saveProject(file);
        } else {
            this.pushError((Throwable)null, "Saving is not allowed without a valid license. Please visit the website to register your copy of Chromatik.");
        }

    }

    public static void log(String message) {
        LX._log(CHROMATIK_PREFIX, message);
    }

    public static void error(Exception x, String message) {
        LX._error(CHROMATIK_PREFIX, x, message);
    }

    public static void error(String message) {
        LX._error(CHROMATIK_PREFIX, message);
    }

    public static void main(String[] args) {
        try {
            if (License.licenseCLI(args)) {
                return;
            }

            LXStudio.Flags flags = new LXStudio.Flags();
            flags.windowTitle = CHROMATIK_PREFIX + " - IQE";
            flags.classpathPlugins.add("org.iqe.LXPluginIQE");

            // Commented out to use relative media paths. Uncomment if causes issues on pi.
            // bootstrapMediaPath(flags, "Chromatik");

            String logFileName = LOG_FILENAME_FORMAT.format(Calendar.getInstance().getTime());
            File logs = new File(LX.Media.LOGS.getDirName());
            if (!logs.exists()) {
              logs.mkdir();
            }
            setLogFile(new File(LX.Media.LOGS.getDirName(), logFileName));

            log("Starting Chromatik version " + Chromatik.VERSION);
            log("Running java " + System.getProperty("java.version") + " " + System.getProperty("java.vendor") + " " + System.getProperty("os.name") + " " + System.getProperty("os.version") + " " + System.getProperty("os.arch"));
            License.everyone_knows_that_java_is_easy_to_decompile__so_i_decided_not_to_needlessly_obfuscate_this_software__but_i_have_spent_a_lot_of_time_working_on_it___if_you_want_to_modify_it_or_have_a_problem_with_the_licensing_i_will_be_happy_to_hear_from_you_directly__please_dont_break_the_eula__instead_just_contact_me__mark_at_chromatik_dot_co();
            File projectFile = null;
            boolean headless = false;

            for(int i = 0; i < args.length; ++i) {
                String arg = args[i];
                if ("--require-license".equals(arg)) {
                    if (License.get().type == License.Type.NONE) {
                        error("License required by --require-license but none found, quitting.");
                        return;
                    }
                } else if ("--headless".equals(arg)) {
                    headless = true;
                } else if ("--opengl".equals(arg)) {
                    flags.useOpenGL = true;
                } else if ("--warnings".equals(arg)) {
                    LX.LOG_WARNINGS = true;
                } else if ("--disable-zeroconf".equals(arg)) {
                    flags.zeroconf = false;
                } else if ("--disable-preferences".equals(arg)) {
                    flags.loadPreferences = false;
                } else if ("--force-output".equals(arg)) {
                    flags.forceOutput = true;
                } else if ("--enable-plugin".equals(arg)) {
                    if (i < args.length - 1) {
                        ++i;
                        flags.enabledPlugins.add(args[i]);
                    } else {
                        error("No plugin class name specified after --enable-plugin");
                    }
                } else if ("--classpath-plugin".equals(arg)) {
                    if (i < args.length - 1) {
                        ++i;
                        flags.classpathPlugins.add(args[i]);
                    } else {
                        error("No plugin class name specified after --classpath-plugin");
                    }
                } else if (arg.endsWith(".lxp")) {
                    if (projectFile != null) {
                        error("Multiple project/schedule files specified on CLI, ignoring " + projectFile.getName());
                    }

                    // JKB note: Possible LX inconsistency, here it's looking under top level path but
                    // but later loadInitialProject() uses Projects media path.
                    // Adding Projects folder here to keep it cleaner.
                    projectFile = new File(LX.Media.PROJECTS.getDirName() + File.separator + arg);
                    if (!projectFile.exists()) {
                        error("Project file: " + projectFile.getName() + " not found");
                        projectFile = null;
                    }
                } else if (arg.endsWith(".lxs")) {
                    if (projectFile != null) {
                        error("Multiple project/schedule files specified on CLI, ignoring " + projectFile.getName());
                    }

                    projectFile = new File(arg);
                    if (!projectFile.exists()) {
                        error("Schedule file: " + projectFile.getName() + " not found");
                        projectFile = null;
                    }
                } else {
                    error("Unrecognized CLI argument, ignoring: " + arg);
                }
            }

            if (headless) {
                log("Headless CLI flag set, running without UI...");
                headless(flags, projectFile);
            } else {
                ChromatikIQE lx = new ChromatikIQE(flags);

                // Schedule a task to load the initial project file at launch
                final File projectFileFinal = projectFile;
                boolean isSchedule = projectFile != null ? projectFile.getName().endsWith(".lxs") : false;
                lx.engine.addTask(() -> {
                    if (isSchedule) {
                        lx.preferences.schedulerEnabled.setValue(true);
                        LX.log("Opening schedule file: " + projectFileFinal);
                        lx.scheduler.openSchedule(projectFileFinal, true);
                    } else {
                        try {
                            lx.preferences.loadInitialProject(projectFileFinal);
                        } catch (Exception var5) {
                            error(var5, "Exception loading initial project: " + var5.getLocalizedMessage());
                        }

                        lx.preferences.loadInitialSchedule();
                    }

                    if (flags.forceOutput) {
                        lx.engine.output.enabled.setValue(true);
                    }

                });
                lx.run();
            }
        } catch (Exception var9) {
            error(var9, "Unhandled exception in Chromatik.main: " + var9.getLocalizedMessage());
        }

    }

    public static void headless(LXStudio.Flags flags, File projectFile) {
        LX lx = new LX(flags) {
            protected final LX.Permissions getPermissions() {
                return ChromatikIQE.createPermissions();
            }
        };
        if (projectFile != null) {
            boolean isSchedule = projectFile.getName().endsWith(".lxs");
            if (!projectFile.exists()) {
                error((isSchedule ? "Schedule" : "Project") + " file does not exist: " + projectFile);
            } else {
                if (isSchedule) {
                    lx.preferences.schedulerEnabled.setValue(true);
                    log("Opening schedule file: " + projectFile);
                    lx.scheduler.openSchedule(projectFile, true);
                } else {
                    log("Opening project file: " + projectFile);
                    lx.openProject(projectFile);
                }

                if (flags.forceOutput) {
                    lx.engine.output.enabled.setValue(true);
                }
            }
        } else {
            error("No project or schedule file specified in headless mode, this will be uneventful...");
        }

        lx.engine.start();
    }
}
