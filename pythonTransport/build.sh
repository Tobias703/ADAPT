#!/usr/bin/env bash
#
# Prerequisites:
#   Python 3.11+
#
# Output:
#   dist/pt_foobar   — standalone ELF binary, no Python installation needed

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
    pt_foobar.spec

echo ""
echo "✓ Build complete:  dist/pt_foobar"
echo ""
echo "Quick smoke test (server mode):"
echo "  TOR_PT_STATE_LOCATION=/tmp/pt_state \\"
echo "  TOR_PT_MANAGED_TRANSPORT_VER=1 \\"
echo "  TOR_PT_SERVER_TRANSPORTS=foobar \\"
echo "  TOR_PT_SERVER_BINDADDR=foobar-127.0.0.1:4911 \\"
echo "  TOR_PT_ORPORT=127.0.0.1:9001 \\"
echo "  ./dist/pt_foobar"
echo ""
echo "Quick smoke test (client mode):"
echo "  TOR_PT_STATE_LOCATION=/tmp/pt_state \\"
echo "  TOR_PT_MANAGED_TRANSPORT_VER=1 \\"
echo "  TOR_PT_CLIENT_TRANSPORTS=foobar \\"
echo "  ./dist/pt_foobar"
