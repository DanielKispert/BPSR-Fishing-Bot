import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    # PyInstaller bundle: assets are in _internal/assets/
    _BASE = Path(sys._MEIPASS)
else:
    _BASE = Path(__file__).resolve().parent.parent

PACKAGE_ROOT = Path(__file__).resolve().parent.parent
ASSETS_PATH = _BASE / "assets"
TEMPLATES_PATH = ASSETS_PATH / "templates"