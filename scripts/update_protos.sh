#!/bin/bash

python -m grpc_tools.protoc -Ishared/protos --python_out=shared --grpc_python_out=shared shared/protos/pokerbot.proto

echo "Proto files have been updated."
