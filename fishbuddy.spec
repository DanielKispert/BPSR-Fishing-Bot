# -*- mode: python ; coding: utf-8 -*-
# fishbuddy.spec: PyInstaller onedir build. Run: pyinstaller fishbuddy.spec
# (or use build.bat which handles all prerequisites)

import sys
from pathlib import Path

ROOT = Path(SPECPATH)
block_cipher = None

added_datas = [
    (str(ROOT / "src" / "fishbot" / "assets" / "templates"), "assets/templates"),
    (str(ROOT / "src" / "fishbot" / "config" / "default_config.toml"), "config"),
    # Tesseract tessdata (uncomment when bundling):
    # (str(ROOT / "vendor" / "tesseract" / "tessdata"), "tessdata"),
]

added_binaries = [
    # Tesseract exe + DLLs (uncomment when bundling):
    # (str(ROOT / "vendor" / "tesseract" / "*.exe"), "."),
    # (str(ROOT / "vendor" / "tesseract" / "*.dll"), "."),
]

hidden_imports = [
    "pynput.keyboard._win32",
    "pynput.mouse._win32",
    "keyboard._winkeyboard",
    "PIL._imagingtk",
    "PIL.Image",
    "PIL.ImageGrab",
    "PyQt6.sip",
    "pydantic.deprecated.class_validators",
]

excluded_modules = [
    "gi", "gi.repository", "gi.repository.Gst",
    "test", "unittest",
    "tkinter", "_tkinter", "tkinter.ttk",
    "matplotlib.tests", "numpy.testing",
]

a = Analysis(
    [str(ROOT / "main.py")],
    pathex=[str(ROOT / "src")],
    binaries=added_binaries,
    datas=added_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excluded_modules,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FishBuddy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=str(ROOT / "installer" / "fishbuddy.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="FishBuddy",
)
