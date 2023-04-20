# With Chromatik

```bash
mvn clean package -DskipTests ; java -XstartOnFirstThread -cp $(find target -name '*.jar'):$HOME/Downloads/Chromatik-alpha/glxstudio-0.4.2-SNAPSHOT-jar-with-dependencies.jar heronarts.lx.studio.Chromatik ../iqe.lxp --classpath-plugin org.iqe.LXPluginIQE
```