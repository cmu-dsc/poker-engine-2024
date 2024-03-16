#!/bin/bash

sudo rm -rf logs
docker compose down
docker compose up --build
