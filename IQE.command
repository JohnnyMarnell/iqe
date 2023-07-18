#!/bin/bash

echo "$(pwd)"
cd "$(dirname $0)"
echo "$(pwd)"

bash "$(pwd)/RUN.sh"
