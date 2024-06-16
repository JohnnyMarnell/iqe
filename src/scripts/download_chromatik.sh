#!/bin/bash
echo "**** ToDo: upgrade to Chromatik v1.0.0, place old jar in vendor" ; exit 0
cd "$(dirname "$0")"
cd ../../

if [[ -f ./vendor/glxstudio.jar ]] ; then
    echo "Chromatik already installed:"
    find ./vendor
else
    platform=$(uname)
    if [[ "$platform" == 'Linux' ]]; then
        platform='linux'
    elif [[ "$platform" == 'Darwin' ]]; then
        platform='macos'
    fi

    arch=$(arch)
    if [[ "$arch" == "arm64" ]] ; then
        arch='aarch64'
    fi

    release_date="$(cat ./VERSION.chromatik)"
    chromatik="Chromatik-alpha-${release_date}-${platform}-${arch}"

    url="https://github.com/heronarts/Chromatik/releases/download/${release_date}/${chromatik}.zip"
    echo "Chromatik installing from $url"
    curl -L "$url" -o /tmp/chromatik.zip
    unzip -o /tmp/chromatik.zip -d vendor
    cp vendor/Chromatik-alpha/glxstudio*.jar vendor/glxstudio.jar
fi