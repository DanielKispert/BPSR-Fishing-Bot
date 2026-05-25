"""
hotkeys.py – thin compatibility shim.

Imports NativeHotkeys (Win32 RegisterHotKey on Windows; keyboard-lib fallback
on macOS/Linux) and re-exports it as ``Hotkeys`` so all existing call-sites
require no changes.

See hotkeys_native.py for the full implementation and Win32 API documentation.
"""

from src.fishbot.core.game.hotkeys_native import NativeHotkeys as Hotkeys

__all__ = ['Hotkeys']
