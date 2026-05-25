"""Tesseract OCR path auto-detection.

Priority order:
  1. Explicit path from config (if not "auto")
  2. Bundled tesseract.exe next to the executable (PyInstaller builds)
  3. Common Windows install locations
  4. System PATH lookup (shutil.which)
  5. Returns None  ->  OCR features are disabled gracefully

Usage:
    from src.fishbot.utils.tesseract_finder import find_tesseract
    path = find_tesseract(config_path="auto")   # or a specific path
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Optional


def find_tesseract(config_path: str = "auto") -> Optional[str]:
    """Locate the Tesseract executable and return its absolute path, or None.

    Args:
        config_path: The ocr.tesseract_path value from config.toml.
                     Pass "auto" (or omit) to enable automatic detection.

    Returns:
        Absolute path string to tesseract.exe, or None if not found.
    """
    # 1. Explicit config path
    if config_path and config_path.strip().lower() != "auto":
        p = Path(config_path)
        if p.exists():
            return str(p)
        _warn(
            f"Configured Tesseract path not found: {config_path}\n"
            "  Falling back to automatic detection."
        )

    # 2. Bundled alongside executable (PyInstaller / packaged builds)
    if getattr(sys, "frozen", False):
        bundled = Path(sys.executable).parent / "tesseract.exe"
        if bundled.exists():
            return str(bundled)

    # 3. Common Windows install locations
    _common = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\Public\Tesseract-OCR\tesseract.exe",
    ]
    for candidate in _common:
        if Path(candidate).exists():
            return candidate

    # 4. System PATH
    found = shutil.which("tesseract")
    if found:
        return found

    # 5. Not found
    return None


def _warn(message: str) -> None:
    """Emit a warning via the bot logger if available, otherwise print."""
    try:
        from src.fishbot.utils.logger import log
        log(f"[WARN] ⚠️  {message}")
    except Exception:
        print(f"[WARN] {message}")
