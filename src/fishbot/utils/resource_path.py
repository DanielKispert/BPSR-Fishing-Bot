"""
resource_path.py
~~~~~~~~~~~~~~~~
Portable path helper for accessing bundled data files in both
development mode and when frozen by PyInstaller.

Usage
-----
    from fishbot.utils.resource_path import resource_path

    # Works in both dev and frozen (dist/) environments:
    cfg_path   = resource_path("config/default_config.toml")
    tmpl_path  = resource_path("assets/templates/connect.png")
    tess_path  = resource_path("tesseract.exe")   # only when bundled

How it works
------------
PyInstaller extracts bundled files to a temporary directory at runtime
and stores its path in sys._MEIPASS.  In development the files live
relative to the project root (two levels above this file's location).

The function returns a resolved absolute Path in both cases, so callers
do not need to worry about the execution context.
"""

from __future__ import annotations

import sys
from pathlib import Path


def resource_path(relative_path: str | Path) -> Path:
    """Return the absolute path to a bundled resource.

    Parameters
    ----------
    relative_path:
        Path relative to the bundle root, e.g. "config/default_config.toml"
        or "assets/templates/connect.png".

    Returns
    -------
    Path
        Resolved absolute path.  The file may not exist yet (e.g. when
        Tesseract is not bundled); callers should check path.exists()
        before using it.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running inside a PyInstaller bundle -- all data files are under
        # sys._MEIPASS (the extraction temp dir or onedir dist folder).
        base = Path(sys._MEIPASS)
    else:
        # Running from source in a development / test environment.
        # This file lives at:  src/fishbot/utils/resource_path.py
        # Project root is three levels up (utils -> fishbot -> src -> root).
        base = Path(__file__).resolve().parent.parent.parent.parent

    return (base / relative_path).resolve()


def config_path(filename: str = "default_config.toml") -> Path:
    """Convenience shortcut for files in the config/ bundle folder."""
    return resource_path(f"config/{filename}")


def template_path(filename: str) -> Path:
    """Convenience shortcut for files in the assets/templates/ folder."""
    return resource_path(f"assets/templates/{filename}")
