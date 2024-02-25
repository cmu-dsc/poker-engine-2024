#!/bin/bash

cd shared

python -m grpc_tools.protoc -Iprotos --python_out=. --grpc_python_out=. protos/pokerbot.proto

cd ..

echo "Proto files have been updated."
