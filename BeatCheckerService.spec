# -*- mode: python ; coding: utf-8 -*-

import sys
import platform
from pathlib import Path


# SPECPATH is provided by PyInstaller (directory containing this spec file)
project_dir = Path(SPECPATH).resolve()
resources_dir = project_dir / "resources" / "ffmpeg"

# Check for platform-specific ffmpeg binary
extra_binaries: list[tuple[str, str]] = []
if platform.system() == "Windows":
    ffmpeg_binary = resources_dir / "ffmpeg.exe"
elif platform.system() == "Darwin":  # macOS
    ffmpeg_binary = resources_dir / "ffmpeg"
else:  # Linux or other
    ffmpeg_binary = resources_dir / "ffmpeg"

if ffmpeg_binary.exists():
    extra_binaries.append((str(ffmpeg_binary), '.'))
    print(f"[BeatCheckerService] Bundling ffmpeg from: {ffmpeg_binary}", file=sys.stderr)
else:
    print(f"[BeatCheckerService] WARNING: ffmpeg binary not found at {ffmpeg_binary}", file=sys.stderr)
    print("[BeatCheckerService] The app will attempt to use system ffmpeg from PATH", file=sys.stderr)


a = Analysis(
    ['main.py'],
    pathex=[str(project_dir)],
    binaries=extra_binaries,
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='BeatCheckerService',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='BeatCheckerService',
)

# macOS-specific: Create .app bundle
if platform.system() == "Darwin":
    app = BUNDLE(
        coll,
        name='BeatCheckerService.app',
        icon=None,
        bundle_identifier='de.designedbycarl.beatchecker.service',
        info_plist={
            'CFBundleDisplayName': 'BeatChecker Service',
            'CFBundleName': 'BeatChecker Service',
            'LSUIElement': True,      # hide Dock icon and App Switcher entry
            'NSUIElement': True,
        },
    )
