#!/bin/sh
cd "$(dirname "$0")"
rm -rf shadow.data/
shadow --template-directory shadow.data.template shadow.yaml > shadow.log