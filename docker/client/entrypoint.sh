#!/bin/sh
set -eu

# Ensure DataDirectory exists and is owned by toruser
mkdir -p /app/data
chmod 700 /app/data

# Tor will use /app/torrc
cd /app
exec tor -f torrc
