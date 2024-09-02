#!/bin/bash

cd "$(dirname $0)"

akill () {
	echo "Killing:" >&2
	ps aux | grep -iP "$@" | grep -v grep >&2
	ps aux | grep -iP "$@" | grep -v grep | awk '{print "kill -9 "$2}' | sh >&2
}

# Function to kill all child processes
cleanup() {
    echo "Cleaning up..."
    pkill -P $$
    akill 'Flamecaster|python.*multiprocessing'
}

# Trap EXIT signal to trigger cleanup
trap cleanup EXIT

# function run_flamecaster() {
#     (
#         akill 'Flamecaster|python.*multiprocessing'
#         cd ../Flamecaster
#         conda activate iqe
#         python -m Flamecaster --file ~/src/iqe/src/main/resources/flamecaster-config.conf
#     )
# }
# run_flamecaster &

cd `dirname $0`

./src/scripts/download_chromatik.sh

./mvnw clean package -DskipTests ;

CMD="java $( [[ $(uname) == 'Darwin' ]] && echo "-XstartOnFirstThread" ) \
    -cp ./target/iqe-1.0-SNAPSHOT-jar-with-dependencies.jar:./vendor/glxstudio.jar \
    heronarts.lx.studio.ChromatikIQE iqe.lxp"

echo "$CMD"
eval "$CMD"
