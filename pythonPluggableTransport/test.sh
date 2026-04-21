#!/bin/sh
cd "$(dirname "$0")"

if [ -z "$1" ]; then
    echo "Usage: ./test.sh <transport name>"
    echo "Example: ./test.sh foobar"
    exit 1
fi

python3 ./test_pt.py -t "$1"