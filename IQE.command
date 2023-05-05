#!/bin/bash
cd `dirname $0`

./mvnw clean package -DskipTests ; \
java -XstartOnFirstThread \
    -cp $(find target -name '*.jar'):$(\
        find "$HOME/Downloads/Chromatik-alpha/" -name 'glxstudio*.jar') \
    heronarts.lx.studio.Chromatik iqe.lxp \
    --classpath-plugin org.iqe.LXPluginIQE

