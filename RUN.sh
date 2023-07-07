#!/bin/bash

cd `dirname $0`

./src/scripts/download_chromatik.sh

./mvnw clean package -DskipTests ;

eval "java $( [[ $(uname) == 'Darwin' ]] && echo "-XstartOnFirstThread" ) \
    -cp ./target/iqe-1.0-SNAPSHOT-jar-with-dependencies.jar:./vendor/glxstudio.jar \
    heronarts.lx.studio.ChromatikIQE iqe.lxp \
    --classpath-plugin org.iqe.LXPluginIQE"

