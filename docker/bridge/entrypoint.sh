#!/bin/sh
set -eu

# Ensure DataDirectory exists and is owned by toruser
mkdir -p /app/data
chmod 700 /app/data

# Tor will use /app/torrc; the command must run in /app (`exec tor -f /app/torrc` is not valid, as tor cannot find the pt-binary that way)
cd /app
exec tor -f torrc
