#!/bin/bash

REPOSITORY_NAME="poker-engine-2024"
TAG="latest"
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID="123456789012"
ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

docker build -f dockerfiles/engine/Dockerfile -t "${REPOSITORY_NAME}:${TAG}" .

docker tag "${REPOSITORY_NAME}:${TAG}" "${ECR_URI}/${REPOSITORY_NAME}:${TAG}"

aws ecr get-login-password --region "${AWS_REGION}" | docker login --username AWS --password-stdin "${ECR_URI}"

docker push "${ECR_URI}/${REPOSITORY_NAME}:${TAG}"
