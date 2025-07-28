#!/bin/bash
docker build -t tsm-android-builder -f Dockerfile.build .
docker run -v $(pwd):/workspace tsm-android-builder \
    ./gradlew assembleRelease
