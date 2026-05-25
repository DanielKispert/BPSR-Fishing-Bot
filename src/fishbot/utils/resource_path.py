"""Portable path helper: resolves bundled data files in both dev and PyInstaller builds."""

from __future__ import annotations
import sys
from pathlib import Path



def resource_path(relative_path: str | Path) -> Path:
    """Return absolute path to a bundled resource (dev or frozen mode)."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)
    else:
        # src/fishbot/utils/ -> project root is 4 levels up
        base = Path(__file__).resolve().parent.parent.parent.parent
    return (base / relative_path).resolve()



def config_path(filename: str = "default_config.toml") -> Path:
    """Shortcut for config/ bundle folder."""
    return resource_path(f"config/{filename}")



def template_path(filename: str) -> Path:
    """Shortcut for assets/templates/ folder."""
    return resource_path(f"assets/templates/{filename}")
