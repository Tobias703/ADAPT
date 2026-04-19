#!/usr/bin/env bash
#
# Prerequisites:
#   Python 3.11+
#
# Output:
#   dist/ppt   - standalone ELF binary, no Python installation needed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "==> Checking Python version"
python3 --version

echo "==> Installing/upgrading PyInstaller"
pip install --quiet --upgrade pyinstaller

echo "==> Building single-file binary"
pyinstaller \
    --clean \
    --noconfirm \
    ppt.spec

echo ""
echo "Build complete:  dist/ppt"
