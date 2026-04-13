#!/bin/sh
cd "$(dirname "$0")"
rm -rf ./shadow.data/
export UID=$(id -u)
export GID=$(id -g)
docker compose up