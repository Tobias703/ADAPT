#!/bin/sh
cd "$(dirname "$0")"
rm -rf ./shadow.data/
export LOCAL_UID=$(id -u)
export LOCAL_GID=$(id -g)
docker compose up