# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_portal.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['src', 'src.config', 'src.crawler', 'src.parser', 'src.exporter', 'src.main', 'src.eurocham_crawler', 'src.eurocham_exporter', 'src.eurocham_main', 'src.portal'],
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
    a.binaries,
    a.datas,
    [],
    name='VN_Directory_Crawler',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
