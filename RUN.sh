#!/bin/bash

cd "$(dirname $0)"

# Function to kill all child processes
cleanup() {
    echo "Cleaning up..."
    pkill -P $$
}

# Trap EXIT signal to trigger cleanup
trap cleanup EXIT

function run_flamecaster() {
    (
        cd ../Flamecaster
        python -m Flamecaster --file ../iqe/src/main/resources/flamecaster-config.conf
    )
}
run_flamecaster &

cd `dirname $0`

./src/scripts/download_chromatik.sh

./mvnw clean package -DskipTests ;

CMD="java $( [[ $(uname) == 'Darwin' ]] && echo "-XstartOnFirstThread" ) \
    -cp ./target/iqe-1.0-SNAPSHOT-jar-with-dependencies.jar:./vendor/glxstudio.jar \
    heronarts.lx.studio.ChromatikIQE iqe.lxp"

echo "$CMD"
eval "$CMD"
