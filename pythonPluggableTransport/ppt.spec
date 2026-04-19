# PyInstaller build specification

# Produces a single-file ELF binary that bundles CPython and all modules.

# Build with the 'build.sh' script

# Output:  dist/pt_foobar

import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[str(Path.cwd())],
    binaries=[],
    datas=[],
    # Explicitly include all our packages so PyInstaller doesn't miss them
    hiddenimports=[
        'transports',
        'transports.foobar',
        'asyncio',
        'asyncio.base_events',
        'asyncio.selector_events',
        'asyncio.unix_events',
        'logging',
        'json',
        'struct',
        'argparse',
        'signal',
        'abc',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ppt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
