# pt_foobar.spec — PyInstaller build specification
#
# Produces a single-file ELF binary that bundles CPython and all modules.
# Shadow runs real ELF binaries, so this lets the PT work in a Shadow
# simulation without requiring Python to be installed in the simulation.
#
# Build:
#   pip install pyinstaller
#   pyinstaller pt_foobar.spec
#
# Output:  dist/pt_foobar   (single ELF, ~7–12 MB)

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
    name='pt_foobar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,          # UPX can confuse Shadow's ELF loader; leave off
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,       # PT is a console app (no GUI)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
