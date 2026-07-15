# -*- mode: python ; coding: utf-8 -*-
"""Production PyInstaller spec for the one-folder Windows runtime."""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

hiddenimports = collect_submodules("vegas_doc.builtin_plugins")
datas = collect_data_files(
    "vegas_doc",
    includes=[
        "resources/templates/*.docx",
        "resources/themes/*.qss",
        "resources/docs/*.txt",
        "resources/scripts/*.ps1",
    ],
)
datas += [
    ("assets/app.ico", "vegas_doc/resources/branding"),
    ("assets/app.png", "vegas_doc/resources/branding"),
    ("assets/vegas_logo.png", "vegas_doc/resources/branding"),
]
excludes = [
    "pytest", "pytest_qt", "pip", "setuptools", "wheel", "distutils",
    "tkinter", "matplotlib", "numpy", "pandas", "scipy", "IPython",
    "notebook", "jupyter", "PIL.ImageQt", "unittest.test",
    "PySide6.Qt3DAnimation", "PySide6.Qt3DCore", "PySide6.Qt3DExtras",
    "PySide6.Qt3DInput", "PySide6.Qt3DLogic", "PySide6.Qt3DRender",
    "PySide6.QtBluetooth", "PySide6.QtCharts", "PySide6.QtConcurrent",
    "PySide6.QtDataVisualization", "PySide6.QtGraphs", "PySide6.QtHelp",
    "PySide6.QtLocation", "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
    "PySide6.QtNetworkAuth", "PySide6.QtNfc", "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "PySide6.QtPositioning", "PySide6.QtQml", "PySide6.QtQuick",
    "PySide6.QtQuick3D", "PySide6.QtQuickControls2", "PySide6.QtQuickWidgets",
    "PySide6.QtRemoteObjects", "PySide6.QtScxml", "PySide6.QtSensors",
    "PySide6.QtSerialBus", "PySide6.QtSerialPort", "PySide6.QtSpatialAudio",
    "PySide6.QtSql", "PySide6.QtStateMachine", "PySide6.QtSvgWidgets",
    "PySide6.QtTest", "PySide6.QtTextToSpeech", "PySide6.QtUiTools",
    "PySide6.QtWebChannel", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineQuick",
    "PySide6.QtWebEngineWidgets", "PySide6.QtWebSockets", "PySide6.QtXml",
]
a = Analysis(
    ["src/main.py"],
    pathex=["src"],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=excludes,
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Vegas_Total_Solution_Doc",
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon="assets/app.ico",
    version="build/version_info.txt",
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Vegas_Total_Solution_Doc")
