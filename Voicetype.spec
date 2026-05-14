# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_all

# Add src to path for analysis
sys.path.append(os.path.abspath('src'))

# Trimming unused Qt modules to reduce size
excluded_modules = [
    'PySide6.QtNetwork', 'PySide6.QtSql', 'PySide6.QtXml', 'PySide6.QtTest',
    'PySide6.QtDBus', 'PySide6.QtPrintSupport', 'PySide6.QtBluetooth',
    'PySide6.QtMultimedia', 'PySide6.QtPositioning', 'PySide6.QtLocation',
    'PySide6.QtSensors', 'PySide6.QtWebEngine', 'PySide6.QtWebChannel',
    'PySide6.QtSvg', 'PySide6.QtQuick', 'PySide6.QtQml', 'PySide6.Qt3D',
    'PySide6.QtCharts', 'PySide6.QtDataVisualization', 'PySide6.QtPdf',
    'PySide6.QtTextToSpeech', 'PySide6.QtSpatialAudio', 'PySide6.QtHttpServer',
    'PySide6.QtDesigner', 'PySide6.QtUiTools', 'PySide6.QtHelp', 'PySide6.QtAxContainer',
    'tkinter', 'unittest'
]

datas = [('src', 'src'), ('assets', 'assets')]
binaries = []
hiddenimports = [
    'pyperclip',
    'sounddevice', 'keyboard', 'PySide6', 'PySide6.QtCore', 
    'PySide6.QtGui', 'PySide6.QtWidgets', 'faster_whisper', 
    'importlib_metadata', 'ctranslate2', 'onnxruntime', 'tokenizers'
]

# Force collect everything for essential packages
essential_pkgs = [
    'pyperclip', 'sounddevice', 'keyboard', 'PySide6',
    'faster_whisper', 'ctranslate2', 'huggingface_hub',
    'onnxruntime', 'tokenizers'
]

for pkg in essential_pkgs:
    tmp_ret = collect_all(pkg)
    datas += tmp_ret[0]
    binaries += tmp_ret[1]
    hiddenimports += tmp_ret[2]

a = Analysis(
    ['run.py'],
    pathex=[os.path.abspath('src')],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove excluded modules from the analysis results
a.binaries = [x for x in a.binaries if not any(excl in x[0] for excl in excluded_modules)]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Voicetype',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False, 
    upx=False,    
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False, # Set to False for a proper windowed GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Voicetype',
)
