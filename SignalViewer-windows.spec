# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_root = Path(SPECPATH)
customtkinter_datas, customtkinter_binaries, customtkinter_hiddenimports = (
    collect_all("customtkinter")
)

a = Analysis(
    [str(project_root / "src" / "main.py")],
    pathex=[str(project_root / "src")],
    binaries=customtkinter_binaries,
    datas=customtkinter_datas,
    hiddenimports=customtkinter_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
a.datas = [
    entry
    for entry in a.datas
    if "matplotlib/mpl-data/sample_data/" not in entry[0].replace("\\", "/")
]
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Signal Viewer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Signal Viewer",
)
