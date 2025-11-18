#!/bin/sh
cd "../$(dirname "$0")"
clear
cargo build
tor -f client-torrc