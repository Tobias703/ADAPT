#!/bin/sh
cd "./$(dirname "$0")"
clear
docker compose up --remove-orphans --build -d