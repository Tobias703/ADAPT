#!/bin/sh
cd "../$(dirname "$0")"
clear
cd docker
docker compose up --remove-orphans --build -d