#!/bin/bash

cd "$(dirname $0)"

# Function to kill all child processes
cleanup() {
    echo "Cleaning up..."
    # Kill any node processes on our ports
    lsof -ti:8282 | xargs kill -9 2>/dev/null || true
    lsof -ti:8080 | xargs kill -9 2>/dev/null || true
    # Kill all child processes
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

function run_control_ui() {
    (
        # Kill any existing process on ports (updated to 8282 for web)
        lsof -ti:8282 | xargs kill -9 2>/dev/null || true
        lsof -ti:8080 | xargs kill -9 2>/dev/null || true
        
        # Give it a moment to release the ports
        sleep 2
        
        # Use nvm if available
        if [ -s "$HOME/.nvm/nvm.sh" ]; then
            source "$HOME/.nvm/nvm.sh"
            nvm use
        fi
        
        # Run from the main iqe directory, not from src/control-ui
        # This uses the parent package.json script which builds then starts
        npm run control
    )
}
run_control_ui &

cd `dirname $0`

./src/scripts/download_chromatik.sh

./mvnw clean package -DskipTests ;

CMD="java $( [[ $(uname) == 'Darwin' ]] && echo "-XstartOnFirstThread" ) \
    -cp ./target/iqe-1.0-SNAPSHOT-jar-with-dependencies.jar:./vendor/glxstudio.jar \
    heronarts.lx.studio.ChromatikIQE iqe.lxp"

echo "$CMD"
eval "$CMD"
