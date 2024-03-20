#!/bin/bash

# rm -rf logs
docker compose down
docker compose build
docker compose up
