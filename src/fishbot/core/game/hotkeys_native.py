"""
hotkeys_native.py – Admin-free hotkey registration via Win32 RegisterHotKey.

Win32 API notes for future maintainers
=======================================
``RegisterHotKey(hwnd, id, fsModifiers, vk)``
    hwnd        – Window handle.  Passing ``None`` (NULL) routes WM_HOTKEY
                  messages into the *calling thread's* message queue, not a
                  specific window.  This is exactly what we want so the
                  dedicated HotkeyThread owns all hotkey messages.
    id          – Integer identifier in range 1–0xBFFF chosen by the caller.
                  Each id must be unique *per thread*.
    fsModifiers – Bit flags: MOD_ALT(0x1), MOD_CONTROL(0x2), MOD_SHIFT(0x4),
                  MOD_WIN(0x8), MOD_NOREPEAT(0x4000).  Pass 0 for bare keys.
    vk          – Windows virtual-key code, e.g. VK_F8 = 0x77.

``GetMessage(&msg, hwnd, 0, 0)``
    Blocks until a message is available.  Returns 0 on WM_QUIT, -1 on error.
    When a registered hotkey is pressed, the system posts WM_HOTKEY (0x0312)
    with msg.wParam == the ``id`` given to RegisterHotKey.

``UnregisterHotKey(hwnd, id)``
    Releases a registered hotkey.  Must use the same hwnd and id.

``PostQuitMessage(exitCode)``
    Posts WM_QUIT to the current thread's queue, causing GetMessage to return 0
    and the message-pump loop to exit cleanly.  Used by _action_stop to shut
    down the message pump from within a callback.

Why this beats the ``keyboard`` library on Windows
===================================================
``keyboard`` installs a system-wide low-level keyboard hook (WH_KEYBOARD_LL)
which requires administrator / elevated privileges on modern Windows versions.
``RegisterHotKey`` has no such requirement – any unprivileged process can use it.
"""

from __future__ import annotations

import multiprocessing
import sys
import threading
from typing import Callable, Dict, List, Optional

from src.fishbot.utils.logger import log
from src.fishbot.utils.roi_visualizer import main as show_roi_visualizer

# ---------------------------------------------------------------------------
# Platform detection and conditional imports
# ---------------------------------------------------------------------------
IS_WINDOWS: bool = sys.platform == "win32"
_HAS_KEYBOARD_LIB: bool = False  # overridden below on non-Windows if available

if IS_WINDOWS:
    import ctypes
    import ctypes.wintypes as wintypes

    # Win32 constants
    WM_HOTKEY: int    = 0x0312
    WM_QUIT: int      = 0x0012
    MOD_NOREPEAT: int = 0x4000  # suppresses auto-repeat; avoids callback spam

    # Virtual-key codes for F-keys and digit keys
    VK_MAP: Dict[str, int] = {
        'F1':  0x70, 'F2':  0x71, 'F3':  0x72, 'F4':  0x73,
        'F5':  0x74, 'F6':  0x75, 'F7':  0x76, 'F8':  0x77,
        'F9':  0x78, 'F10': 0x79, 'F11': 0x7A, 'F12': 0x7B,
        '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
        '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    }

    # Minimal MSG structure for GetMessage
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
    # Explicit restypes prevent truncation on 64-bit Python
    _user32.RegisterHotKey.restype      = wintypes.BOOL
    _user32.UnregisterHotKey.restype    = wintypes.BOOL
    _user32.GetMessage.restype          = wintypes.BOOL
    _user32.PostQuitMessage.restype     = None
    _user32.PostThreadMessageW.restype  = wintypes.BOOL
    _user32.GetCurrentThreadId.restype  = wintypes.DWORD

else:
    # Non-Windows: try the keyboard library as a fallback
    try:
        import keyboard as _keyboard_lib  # type: ignore[import]
        _HAS_KEYBOARD_LIB = True
        log("[WARN] Win32 hotkeys unavailable on '%s'. "
            "Falling back to 'keyboard' library (may need elevated privileges)." % sys.platform)
    except ImportError:
        log("[ERROR] Neither Win32 hotkeys nor the 'keyboard' library is available. "
            "Hotkeys will be DISABLED.")


# ---------------------------------------------------------------------------
# NativeHotkeys
# ---------------------------------------------------------------------------

class NativeHotkeys:
    """
    Admin-free hotkey manager for the fishing bot.

    **Windows**: uses Win32 ``RegisterHotKey`` via ctypes.  A dedicated
    daemon thread runs a ``GetMessage`` loop so hotkeys are always serviced,
    even when the main thread is blocked in a long detection cycle.
    The F8 emergency stop is therefore *guaranteed* to fire.

    **macOS / Linux**: transparently falls back to the ``keyboard`` library
    (if installed) so development on non-Windows machines is unaffected.

    Public attributes
    -----------------
    paused : bool
        ``True`` while the bot should NOT be running.  The main loop in
        ``main.py`` reads this attribute to decide whether to call
        ``bot.update()``.

    Default key bindings
    --------------------
    F6  – Start / resume  (normal mode, no screenshots)
    F7  – Pause
    F8  – Emergency stop  ← fires from its own thread, always reliable
    F9  – Start / resume  (debug mode, screenshots enabled)
    F10 – Toggle burst screenshots
    F11 – Toggle ROI visualiser
    """

    # Win32 hotkey IDs – arbitrary integers, unique within the registering thread.
    # Range: 1 – 0xBFFF (per MSDN; 0xC000–0xFFFF are reserved for atoms).
    _ID_START_NORMAL: int = 1
    _ID_PAUSE:        int = 2
    _ID_STOP:         int = 3
    _ID_START_DEBUG:  int = 4
    _ID_BURST:        int = 5
    _ID_VISUALIZER:   int = 6

    def __init__(self, bot, hotkeys_config: Optional[Dict[str, str]] = None) -> None:
        """
        Parameters
        ----------
        bot:
            The FishingBot instance whose state is controlled via hotkeys.
        hotkeys_config:
            Optional dict mapping action name to key string, e.g.
            ``{'stop': 'F12'}``.  Unspecified actions use their defaults.
            Valid action names: ``start``, ``start_debug``, ``pause``,
            ``stop``, ``burst``, ``visualizer``.
        """
        self.bot = bot
        self.paused: bool = True
        self.visualizer_process: Optional[multiprocessing.Process] = None

        self._stop_event: threading.Event = threading.Event()
        self._win32_thread_id: Optional[int] = None  # set from inside hotkey thread

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

        self._thread = threading.Thread(
            target=self._run,
            name='HotkeyThread',
            daemon=True,  # automatically exits when the main process ends
        )
        self._thread.start()

    # ------------------------------------------------------------------
    # Hotkey action callbacks
    # (called from HotkeyThread; keep them short and thread-safe)
    # ------------------------------------------------------------------

    def _action_start_normal(self) -> None:
        """F6 – Start the bot in normal mode (no debug screenshots)."""
        self.bot.debug_mode = False
        self.bot.detector.screenshots_enabled = False
        self.paused = False
        log("[HOTKEY] ▶ Bot RUNNING (normal mode).")

    def _action_start_debug(self) -> None:
        """F9 – Start the bot in debug mode (screenshots enabled)."""
        self.bot.debug_mode = True
        self.bot.detector.screenshots_enabled = True
        self.paused = False
        log("[HOTKEY] 🐛 Bot RUNNING (DEBUG mode – screenshots enabled).")

    def _action_pause(self) -> None:
        """F7 – Pause the bot (stops update calls without terminating it)."""
        self.paused = True
        log("[HOTKEY] ⏸ Bot PAUSED.")

    def _action_stop(self) -> None:
        """
        F8 – Emergency stop.

        Runs on HotkeyThread, so it fires even when the main thread is blocked.
        Terminates any open visualiser subprocess, signals the bot to stop,
        then posts WM_QUIT to this thread so the message-pump loop exits and
        all hotkeys are unregistered before the thread returns.
        """
        self.paused = True
        log("[HOTKEY] 🛑 EMERGENCY STOP – shutting down bot...")
        if self.visualizer_process and self.visualizer_process.is_alive():
            self.visualizer_process.terminate()
            self.visualizer_process = None
        self.bot.stop()
        self._stop_event.set()
        if IS_WINDOWS:
            # PostQuitMessage posts WM_QUIT to *this* thread's queue.
            # GetMessage will return 0 on the next iteration, exiting the loop.
            _user32.PostQuitMessage(0)

    def _action_toggle_visualizer(self) -> None:
        """F11 – Open or close the ROI visualiser subprocess."""
        if self.visualizer_process and self.visualizer_process.is_alive():
            log("[HOTKEY] 🗺 Closing ROI visualiser.")
            self.visualizer_process.terminate()
            self.visualizer_process = None
        else:
            log("[HOTKEY] 🗺 Opening ROI visualiser.")
            self.visualizer_process = multiprocessing.Process(
                target=show_roi_visualizer, daemon=True
            )
            self.visualizer_process.start()

    def _action_toggle_burst(self) -> None:
        """F10 – Toggle burst (every-frame) screenshot capture."""
        self.bot.detector.burst_screenshots_enabled = (
            not self.bot.detector.burst_screenshots_enabled
        )
        state = "ENABLED" if self.bot.detector.burst_screenshots_enabled else "DISABLED"
        log("[HOTKEY] 📸⚡ Burst screenshots %s." % state)

    # ------------------------------------------------------------------
    # Thread entry point
    # ------------------------------------------------------------------

    def _run(self) -> None:
        """Dispatch to the platform-appropriate hotkey backend."""
        if IS_WINDOWS:
            self._run_win32()
        elif _HAS_KEYBOARD_LIB:
            self._run_keyboard_fallback()
        else:
            log("[ERROR] [HOTKEY] No hotkey backend available – hotkeys are DISABLED.")

    # ------------------------------------------------------------------
    # Win32 message-pump backend
    # ------------------------------------------------------------------

    def _run_win32(self) -> None:
        """
        Win32 RegisterHotKey + GetMessage message-pump loop.

        Execution flow
        --------------
        1. Record the Win32 thread ID (``GetCurrentThreadId``) so that
           ``shutdown()`` can post WM_QUIT from the main thread.
        2. Call ``RegisterHotKey`` for every configured binding.
        3. Enter the ``GetMessage`` blocking loop.
        4. On ``WM_HOTKEY``: look up and invoke the mapped callback.
        5. On ``WM_QUIT`` (``GetMessage`` returns 0): exit the loop.
        6. Call ``UnregisterHotKey`` for every successfully registered id.
        """
        self._win32_thread_id = _user32.GetCurrentThreadId()

        registered_ids: List[int] = []
        for action, key_name in self._key_bindings.items():
            hk_id = self._action_to_id[action]
            vk = VK_MAP.get(key_name.upper())
            if vk is None:
                log("[WARN] [HOTKEY] Unknown key '%s' for action '%s' – skipping." % (key_name, action))
                continue
            ok = _user32.RegisterHotKey(None, hk_id, MOD_NOREPEAT, vk)
            if ok:
                registered_ids.append(hk_id)
            else:
                err = ctypes.GetLastError()
                log("[WARN] [HOTKEY] RegisterHotKey('%s', id=%d) failed (WinError %d). "
                    "Key may already be claimed by another app." % (key_name, hk_id, err))

        desc = ', '.join("'%s'=%s" % (v, k) for k, v in self._key_bindings.items())
        log("[INFO] ✅ Hotkeys registered (Win32): %s" % desc)

        msg = _MSG()
        while True:
            result = _user32.GetMessage(ctypes.byref(msg), None, 0, 0)
            if result <= 0:
                # 0  → WM_QUIT (clean exit requested)
                # -1 → error (GetLastError() would give details)
                break
            if msg.message == WM_HOTKEY:
                callback = self._id_to_callback.get(msg.wParam)
                if callback:
                    try:
                        callback()
                    except Exception as exc:
                        log("[ERROR] [HOTKEY] Callback raised an exception: %s" % exc)

        # Always unregister, even on error exit
        for hk_id in registered_ids:
            _user32.UnregisterHotKey(None, hk_id)
        log("[INFO] [HOTKEY] All Win32 hotkeys unregistered.")

    # ------------------------------------------------------------------
    # keyboard-library fallback (non-Windows)
    # ------------------------------------------------------------------

    def _run_keyboard_fallback(self) -> None:
        """
        Non-Windows fallback using the ``keyboard`` library.

        Registers the same callbacks, then blocks on ``_stop_event``.
        All hooks are removed when the event is set (either by F8 or by
        calling ``shutdown()``).
        """
        import keyboard as kb  # already confirmed available (_HAS_KEYBOARD_LIB)

        for action, key_name in self._key_bindings.items():
            hk_id = self._action_to_id[action]
            callback = self._id_to_callback[hk_id]
            try:
                kb.add_hotkey(key_name.lower(), callback)
            except Exception as exc:
                log("[WARN] [HOTKEY] keyboard.add_hotkey('%s') failed: %s" % (key_name, exc))

        desc = ', '.join("'%s'=%s" % (v, k) for k, v in self._key_bindings.items())
        log("[INFO] ✅ Hotkeys registered (keyboard fallback): %s" % desc)

        self._stop_event.wait()  # block until shutdown() or _action_stop()
        kb.unhook_all()
        log("[INFO] [HOTKEY] keyboard fallback hooks removed.")

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def shutdown(self) -> None:
        """
        Signal the hotkey thread to stop and wait for it to finish.

        Call this from the main thread after the bot loop exits to ensure
        hotkeys are properly unregistered before the process terminates.
        Safe to call multiple times (idempotent).
        """
        if self._stop_event.is_set():
            return  # already stopped (e.g. F8 was pressed)
        self._stop_event.set()
        if IS_WINDOWS and self._win32_thread_id is not None:
            # Post WM_QUIT to unblock GetMessage in the hotkey thread
            _user32.PostThreadMessageW(self._win32_thread_id, WM_QUIT, 0, 0)
        self._thread.join(timeout=2.0)
        log("[INFO] [HOTKEY] Shutdown complete.")
