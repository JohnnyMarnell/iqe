package heronarts.lx.studio;

import heronarts.lx.LX;
import org.iqe.LXPluginIQE;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.net.URL;
import java.nio.file.CopyOption;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.nio.file.StandardOpenOption;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.Calendar;

/**
 * TODO: Temporarily using decompiled Main until I get toolchain correctly setup
 *      Additionally, this helps with showing available CLI args and their code paths.
 *
 * TODO: I also need this because I can't follow how to hook into the UI otherwise?
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

    public static UI ui;
    @Override
    protected UI buildUI() throws IOException {
        ChromatikIQE.ui = super.buildUI();
        LXPluginIQE.hack(ChromatikIQE.ui);
        return ChromatikIQE.ui;
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

    private static boolean bootstrapExampleMedia(String[] args, File media) {
        boolean installExamples = false;
        String[] var6 = args;
        int var5 = args.length;

        for(int var4 = 0; var4 < var5; ++var4) {
            String arg = var6[var4];
            if ("--install-examples".equals(arg)) {
                installExamples = true;
                break;
            }
        }

        bootstrapExampleMedia(media, LX.Media.FIXTURES, installExamples, "/fixtures/", "Cube.lxf", "1", "Fan.lxf", "2", "Square.lxf", "3");
        bootstrapExampleMedia(media, LX.Media.MODELS, installExamples, "/models/", "Cubes.lxm", "1");
        return installExamples;
    }

    private static void bootstrapExampleMedia(File mediaDir, LX.Media mediaType, boolean overwrite, String resourcePrefix, String... paths) {
        try {
            File media = new File(mediaDir, mediaType.getDirName());
            File examples = new File(media, "Examples");
            if (!examples.exists()) {
                examples.mkdir();
            }

            int existingVersion = 0;
            int maxVersion = 0;
            File versionFile = new File(examples, ".version");
            if (!overwrite && versionFile.exists()) {
                existingVersion = Integer.parseInt((new String(Files.readAllBytes(versionFile.toPath()))).trim());
            }

            for(int i = 0; i < paths.length; i += 2) {
                String path = paths[i];
                int version = Integer.parseInt(paths[i + 1]);
                if (version > maxVersion) {
                    maxVersion = version;
                }

                if (version > existingVersion) {
                    String urlString = resourcePrefix + path;
                    URL url = ChromatikIQE.class.getResource(urlString);
                    if (url == null) {
                        error("Example media resource does not exist: " + urlString);
                    } else {
                        Throwable var15 = null;
                        Object var16 = null;

                        try {
                            InputStream is = url.openConnection().getInputStream();

                            try {
                                Path output = (new File(examples, path)).toPath();
                                log("Installing example file: " + output);
                                Files.copy(is, output, new CopyOption[]{StandardCopyOption.REPLACE_EXISTING});
                            } finally {
                                if (is != null) {
                                    is.close();
                                }

                            }
                        } catch (Throwable var26) {
                            if (var15 == null) {
                                var15 = var26;
                            } else if (var15 != var26) {
                                var15.addSuppressed(var26);
                            }

                            throw new RuntimeException(var15);
                        }
                    }
                }
            }

            Files.write(versionFile.toPath(), String.valueOf(maxVersion).getBytes("UTF-8"), new OpenOption[]{StandardOpenOption.CREATE});
        } catch (Exception var27) {
            error(var27, "Could not install example media: " + var27.getMessage());
        }

    }

    public static void log(String message) {
        LX._log("Chromatik", message);
    }

    public static void error(Exception x, String message) {
        LX._error("Chromatik", x, message);
    }

    public static void error(String message) {
        LX._error("Chromatik", message);
    }

    public static void main(String[] args) {
        try {
            if (License.licenseCLI(args)) {
                return;
            }

            LXStudio.Flags flags = new LXStudio.Flags();
            File media = bootstrapMediaPath(flags, "Chromatik");
            if (bootstrapExampleMedia(args, media)) {
                log("Re-installed example content.");
                return;
            }

            String logFileName = LOG_FILENAME_FORMAT.format(Calendar.getInstance().getTime());
            setLogFile(new File(flags.mediaPath, LX.Media.LOGS.getDirName() + File.separator + logFileName));
            log("Starting Chromatik version 0.4.2-SNAPSHOT");
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

                    projectFile = new File(arg);
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
                boolean isSchedule = projectFile != null ? projectFile.getName().endsWith(".lxs") : false;
                final File projectFileFinal = projectFile;
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
