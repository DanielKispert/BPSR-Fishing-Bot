"""Locate Tesseract OCR executable (explicit path -> bundled -> common dirs -> PATH)."""

from __future__ import annotations
import shutil
import sys
from pathlib import Path
from typing import Optional


def find_tesseract(config_path: str = "auto") -> Optional[str]:
    """Return absolute path to tesseract.exe, or None if not found."""
    if config_path and config_path.strip().lower() != "auto":
        p = Path(config_path)
        if p.exists():
            return str(p)
        _warn(f"Configured Tesseract path not found: {config_path} -- falling back to auto-detection.")

    if getattr(sys, "frozen", False):
        bundled = Path(sys.executable).parent / "tesseract.exe"
        if bundled.exists():
            return str(bundled)

    for candidate in [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        r"C:\Users\Public\Tesseract-OCR\tesseract.exe",
    ]:
        if Path(candidate).exists():
            return candidate

    found = shutil.which("tesseract")
    return found if found else None


def _warn(message: str) -> None:
    try:
        from src.fishbot.utils.logger import log
        log(f"[WARN] {message}")
    except Exception:
        print(f"[WARN] {message}")
