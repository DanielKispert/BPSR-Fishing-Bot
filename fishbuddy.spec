# -*- mode: python ; coding: utf-8 -*-
#
# fishbuddy.spec  PyInstaller build specification for FishBuddy
#
# Build command (from repo root):
#   pyinstaller fishbuddy.spec
#
# Or use build.bat which handles all prerequisites automatically.
#
# Output: dist/FishBuddy/  (onedir mode  single folder, NOT a single .exe)
#
# WHY onedir and not onefile?
#   --onefile extracts to a temp directory on every launch, which triggers
#   AV heuristics (self-extracting behaviour). onedir is transparent to
#   security software and starts faster.
#
# WHY --noupx?
#   UPX-compressed executables are flagged by many AV engines. Skip it.
#
# 
# resource_path() helper  how bundled files are accessed at runtime
# 
# When frozen by PyInstaller, all data files land under sys._MEIPASS.
# Use src/fishbot/utils/resource_path.py instead of raw __file__ paths:
#
#   from fishbot.utils.resource_path import resource_path
#   cfg = resource_path("config/default_config.toml")
#   template = resource_path("assets/templates/connect.png")
#
# 

import sys
from pathlib import Path

# Repo root (same directory as this spec file)
ROOT = Path(SPECPATH)

block_cipher = None

# 
# Data files bundled into the package
# Tuples: (source_path, destination_folder_inside_dist)
# 
added_datas = [
    # Template images used by the vision/detection system
    (str(ROOT / "src" / "fishbot" / "assets" / "templates"), "assets/templates"),

    # Default configuration TOML  the app reads this on first run
    (str(ROOT / "src" / "fishbot" / "config" / "default_config.toml"), "config"),

    #  Tesseract OCR data (uncomment when bundling Tesseract) 
    # Step 1: copy tesseract.exe and its DLLs into a local folder, e.g.
    #         vendor/tesseract/
    # Step 2: copy the tessdata/ language files into vendor/tesseract/tessdata/
    # Step 3: uncomment the two lines below:
    #
    # (str(ROOT / "vendor" / "tesseract" / "tessdata"), "tessdata"),
    # 
]

# 
# Binary files (compiled .dll / .exe dependencies)
# 
added_binaries = [
    #  Tesseract executable (uncomment when bundling Tesseract) 
    # Download Tesseract for Windows from:
    #   https://github.com/UB-Mannheim/tesseract/wiki
    # Copy tesseract.exe and all required DLLs into vendor/tesseract/, then
    # uncomment the glob below to bundle the entire folder:
    #
    # (str(ROOT / "vendor" / "tesseract" / "*.exe"), "."),
    # (str(ROOT / "vendor" / "tesseract" / "*.dll"), "."),
    # 
]

# 
# Hidden imports  modules PyInstaller cannot detect via static analysis
# (dynamic imports, platform-specific backend plugins, etc.)
# 
hidden_imports = [
    # pynput: PyAutoGUI uses pynput internally; the Win32 backends are loaded
    # lazily and won't be detected without explicit listing.
    "pynput.keyboard._win32",
    "pynput.mouse._win32",

    # keyboard: low-level Win32 hook backend
    "keyboard._winkeyboard",

    # Pillow: PyAutoGUI screenshot path pulls in these modules dynamically
    "PIL._imagingtk",
    "PIL.Image",
    "PIL.ImageGrab",

    # PyQt6: ensure the platform plugin loader is included
    "PyQt6.sip",

    # pydantic v2 internal validator (loaded at runtime)
    "pydantic.deprecated.class_validators",
]

# 
# Modules to EXCLUDE  saves ~50 MB from the distribution folder
# 
excluded_modules = [
    # GStreamer multimedia framework  not needed for a fishing bot
    "gi",
    "gi.repository",
    "gi.repository.Gst",

    # Standard library test suites
    "test",
    "unittest",

    # tkinter  we use PyQt6; pulling in Tk doubles the size for no reason
    "tkinter",
    "_tkinter",
    "tkinter.ttk",

    # Matplotlib / numpy test fixtures
    "matplotlib.tests",
    "numpy.testing",
]

a = Analysis(
    # Entry point  the top-level main.py at the repo root
    [str(ROOT / "main.py")],

    pathex=[str(ROOT / "src")],   # Add src/ so "from fishbot.*" resolves

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
    [],                          # No binaries merged into exe (onedir mode)
    exclude_binaries=True,       # Binaries stay in the dist folder alongside exe
    name="FishBuddy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                   # --noupx: avoids AV false-positive heuristics
    console=False,               # --windowed: no black console window for users
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,

    #  Icon (uncomment once you have a .ico file) 
    # icon=str(ROOT / "installer" / "fishbuddy.ico"),
    # 
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,                   # --noupx here too (applies to collected DLLs)
    upx_exclude=[],
    name="FishBuddy",            # Output folder: dist/FishBuddy/
)
