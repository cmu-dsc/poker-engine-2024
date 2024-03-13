#!/bin/bash

IMAGE_NAME="pokerbot"
TIMESTAMP=$(date +%m%d%H%M)
TAG="v${TIMESTAMP}"

docker build -f dockerfiles/python_skeleton/Dockerfile -t "${IMAGE_NAME}:${TAG}" .
