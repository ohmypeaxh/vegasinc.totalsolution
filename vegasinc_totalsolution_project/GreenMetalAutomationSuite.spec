
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = collect_all("keyring")
pyside_datas, pyside_bins, pyside_hidden = collect_all("PySide6")
datas += pyside_datas
binaries += pyside_bins
hiddenimports += pyside_hidden

a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, a.binaries, a.datas, [],
    name="GreenMetalAutomationSuite",
    console=False,
    icon="assets/app.ico",
)
