#!/usr/bin/env bash
#
# Prerequisites:
#   Python 3.11+
#
# Output:
#   dist/ppt   - standalone ELF binary, no Python installation needed

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$(cd "$SCRIPT_DIR/.." && pwd)/.venv"

if [[ -x "$VENV_DIR/bin/python" ]]; then
    echo "==> Using existing virtual environment at $VENV_DIR"
else
    echo "==> Creating virtual environment at $VENV_DIR"
    rm -rf "$VENV_DIR"
    python3 -m venv "$VENV_DIR"
fi

PYTHON="$VENV_DIR/bin/python"

echo "==> Checking Python version"
"$PYTHON" --version

echo "==> Installing/upgrading PyInstaller"
"$PYTHON" -m pip install --upgrade pip pyinstaller

echo "==> Building single-file binary"
"$VENV_DIR/bin/pyinstaller" \
    --clean \
    --noconfirm \
    ppt.spec

rm -rf ./build

echo ""
echo "Build complete, the PT-binary can be found here: ./dist/ppt"