#!/bin/sh
cd "../$(dirname "$0")"
clear
# docker build --no-cache -t docker-pt .
docker build -t docker-pt .
docker compose up --remove-orphans -d