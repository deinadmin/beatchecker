# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[('/opt/homebrew/bin/ffmpeg', '.')],
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
