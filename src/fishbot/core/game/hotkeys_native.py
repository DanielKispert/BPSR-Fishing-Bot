"""hotkeys_native.py -- Admin-free hotkey registration via Win32 RegisterHotKey."""

from __future__ import annotations

import multiprocessing
import sys
import threading
from typing import Callable, Dict, List, Optional

from src.fishbot.utils.logger import log
from src.fishbot.utils.roi_visualizer import main as show_roi_visualizer

IS_WINDOWS: bool = sys.platform == "win32"
_HAS_KEYBOARD_LIB: bool = False

if IS_WINDOWS:
    import ctypes
    import ctypes.wintypes as wintypes

    WM_HOTKEY: int    = 0x0312
    WM_QUIT: int      = 0x0012
    MOD_NOREPEAT: int = 0x4000

    VK_MAP: Dict[str, int] = {
        'F1':  0x70, 'F2':  0x71, 'F3':  0x72, 'F4':  0x73,
        'F5':  0x74, 'F6':  0x75, 'F7':  0x76, 'F8':  0x77,
        'F9':  0x78, 'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B,
        '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
        '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    }

    class _MSG(ctypes.Structure):
        _fields_ = [
            ('hwnd',    wintypes.HWND),
            ('message', wintypes.UINT),
            ('wParam',  wintypes.WPARAM),
            ('lParam',  wintypes.LPARAM),
            ('time',    wintypes.DWORD),
            ('pt',      wintypes.POINT),
        ]

    _user32 = ctypes.windll.user32
    _user32.RegisterHotKey.restype     = wintypes.BOOL
    _user32.UnregisterHotKey.restype   = wintypes.BOOL
    _user32.GetMessage.restype         = wintypes.BOOL
    _user32.PostQuitMessage.restype    = None
    _user32.PostThreadMessageW.restype = wintypes.BOOL
    _user32.GetCurrentThreadId.restype = wintypes.DWORD

else:
    try:
        import keyboard as _keyboard_lib  # type: ignore[import]
        _HAS_KEYBOARD_LIB = True
    except ImportError:
        pass


class NativeHotkeys:
    """Admin-free hotkey manager using Win32 RegisterHotKey (Windows) or keyboard lib fallback.

    F6=start, F7=pause, F8=emergency stop, F9=start+debug, F10=burst screenshots, F11=ROI visualiser.
    Keys are configurable via hotkeys_config dict passed to __init__.
    """

    _ID_START_NORMAL: int = 1
    _ID_PAUSE:        int = 2
    _ID_STOP:         int = 3
    _ID_START_DEBUG:  int = 4
    _ID_BURST:        int = 5
    _ID_VISUALIZER:   int = 6

    def __init__(self, bot, hotkeys_config: Optional[Dict[str, str]] = None) -> None:
        """Init hotkeys. hotkeys_config maps action names to key strings (e.g. {'stop': 'F12'})."""
        self.bot = bot
        self.paused: bool = True
        self.visualizer_process: Optional[multiprocessing.Process] = None

        self._stop_event: threading.Event = threading.Event()
        self._win32_thread_id: Optional[int] = None

        # TODO: Make hotkeys configurable via config.toml (HotkeysConfig not yet wired up)
        cfg = hotkeys_config or {}
        self._key_bindings: Dict[str, str] = {
            'start':       cfg.get('start',       'F6'),
            'pause':       cfg.get('pause',       'F7'),
            'stop':        cfg.get('stop',        'F8'),
            'start_debug': cfg.get('start_debug', 'F9'),
            'burst':       cfg.get('burst',       'F10'),
            'visualizer':  cfg.get('visualizer',  'F11'),
        }

        self._action_to_id: Dict[str, int] = {
            'start':       self._ID_START_NORMAL,
            'pause':       self._ID_PAUSE,
            'stop':        self._ID_STOP,
            'start_debug': self._ID_START_DEBUG,
            'burst':       self._ID_BURST,
            'visualizer':  self._ID_VISUALIZER,
        }

        self._id_to_callback: Dict[int, Callable[[], None]] = {
            self._ID_START_NORMAL: self._action_start_normal,
            self._ID_PAUSE:        self._action_pause,
            self._ID_STOP:         self._action_stop,
            self._ID_START_DEBUG:  self._action_start_debug,
            self._ID_BURST:        self._action_toggle_burst,
            self._ID_VISUALIZER:   self._action_toggle_visualizer,
        }

        self._thread = threading.Thread(target=self._run, name='HotkeyThread', daemon=True)
        self._thread.start()

    def _action_start_normal(self) -> None:
        """F6 -- Start the bot in normal mode."""
        self.bot.debug_mode = False
        self.bot.detector.screenshots_enabled = False
        self.paused = False
        log("[HOTKEY] \u25b6 Bot RUNNING (normal mode).")

    def _action_start_debug(self) -> None:
        """F9 -- Start the bot in debug mode (screenshots enabled)."""
        self.bot.debug_mode = True
        self.bot.detector.screenshots_enabled = True
        self.paused = False
        log("[HOTKEY] \U0001f41b Bot RUNNING (DEBUG mode -- screenshots enabled).")

    def _action_pause(self) -> None:
        """F7 -- Pause the bot."""
        self.paused = True
        log("[HOTKEY] \u23f8 Bot PAUSED.")

    def _action_stop(self) -> None:
        """F8 -- Emergency stop (runs on HotkeyThread, fires even if main thread is blocked)."""
        self.paused = True
        log("[HOTKEY] \U0001f6d1 EMERGENCY STOP -- shutting down bot...")
        if self.visualizer_process and self.visualizer_process.is_alive():
            self.visualizer_process.terminate()
            self.visualizer_process = None
        self.bot.stop()
        self._stop_event.set()
        if IS_WINDOWS:
            _user32.PostQuitMessage(0)

    def _action_toggle_visualizer(self) -> None:
        """F11 -- Open or close the ROI visualiser subprocess."""
        if self.visualizer_process and self.visualizer_process.is_alive():
            log("[HOTKEY] \U0001f5fa Closing ROI visualiser.")
            self.visualizer_process.terminate()
            self.visualizer_process = None
        else:
            log("[HOTKEY] \U0001f5fa Opening ROI visualiser.")
            self.visualizer_process = multiprocessing.Process(
                target=show_roi_visualizer, daemon=True
            )
            self.visualizer_process.start()

    def _action_toggle_burst(self) -> None:
        """F10 -- Toggle burst screenshot capture."""
        self.bot.detector.burst_screenshots_enabled = (
            not self.bot.detector.burst_screenshots_enabled
        )
        state = "ENABLED" if self.bot.detector.burst_screenshots_enabled else "DISABLED"
        log("[HOTKEY] \U0001f4f8\u26a1 Burst screenshots %s." % state)

    def _run(self) -> None:
        """Dispatch to the platform-appropriate hotkey backend."""
        if IS_WINDOWS:
            self._run_win32()
        elif _HAS_KEYBOARD_LIB:
            log("[WARN] Win32 hotkeys unavailable on '%s'. "
                "Falling back to 'keyboard' library (may need elevated privileges)." % sys.platform)
            self._run_keyboard_fallback()
        else:
            log("[ERROR] Neither Win32 hotkeys nor the 'keyboard' library is available. "
                "Hotkeys will be DISABLED.")

    def _run_win32(self) -> None:
        """Win32 RegisterHotKey + GetMessage loop. Unregisters all keys on exit."""
        self._win32_thread_id = _user32.GetCurrentThreadId()

        registered_ids: List[int] = []
        for action, key_name in self._key_bindings.items():
            hk_id = self._action_to_id[action]
            vk = VK_MAP.get(key_name.upper())
            if vk is None:
                log("[WARN] [HOTKEY] Unknown key '%s' for action '%s' -- skipping." % (key_name, action))
                continue
            ok = _user32.RegisterHotKey(None, hk_id, MOD_NOREPEAT, vk)
            if ok:
                registered_ids.append(hk_id)
            else:
                err = ctypes.GetLastError()
                log("[WARN] [HOTKEY] RegisterHotKey('%s', id=%d) failed (WinError %d). "
                    "Key may already be claimed by another app." % (key_name, hk_id, err))

        desc = ', '.join("'%s'=%s" % (v, k) for k, v in self._key_bindings.items())
        log("[INFO] \u2705 Hotkeys registered (Win32): %s" % desc)

        msg = _MSG()
        while True:
            if self._stop_event.is_set():
                break
            result = _user32.GetMessage(ctypes.byref(msg), None, 0, 0)
            if result <= 0:
                break
            if msg.message == WM_HOTKEY:
                callback = self._id_to_callback.get(msg.wParam)
                if callback:
                    try:
                        callback()
                    except Exception as exc:
                        log("[ERROR] [HOTKEY] Callback raised an exception: %s" % exc)

        for hk_id in registered_ids:
            _user32.UnregisterHotKey(None, hk_id)
        log("[INFO] [HOTKEY] All Win32 hotkeys unregistered.")

    def _run_keyboard_fallback(self) -> None:
        """Non-Windows fallback using the keyboard library."""
        import keyboard as kb

        for action, key_name in self._key_bindings.items():
            hk_id = self._action_to_id[action]
            callback = self._id_to_callback[hk_id]
            try:
                kb.add_hotkey(key_name.lower(), callback)
            except Exception as exc:
                log("[WARN] [HOTKEY] keyboard.add_hotkey('%s') failed: %s" % (key_name, exc))

        desc = ', '.join("'%s'=%s" % (v, k) for k, v in self._key_bindings.items())
        log("[INFO] \u2705 Hotkeys registered (keyboard fallback): %s" % desc)

        self._stop_event.wait()
        kb.unhook_all()
        log("[INFO] [HOTKEY] keyboard fallback hooks removed.")

    def shutdown(self) -> None:
        """Signal the hotkey thread to stop and wait for it to finish (idempotent)."""
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        if IS_WINDOWS and self._win32_thread_id:
            if self._thread and self._thread.is_alive():
                _user32.PostThreadMessageW(self._win32_thread_id, WM_QUIT, 0, 0)
        self._thread.join(timeout=2.0)
        log("[INFO] [HOTKEY] Shutdown complete.")
