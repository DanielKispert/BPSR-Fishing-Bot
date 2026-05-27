import ctypes
import ctypes.wintypes as wintypes

from src.fishbot.utils.logger import log

_user32 = ctypes.windll.user32
_user32.IsWindowVisible.restype = wintypes.BOOL
_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.GetWindowTextW.restype = ctypes.c_int
_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetWindowTextLengthW.restype = ctypes.c_int
_user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
_user32.EnumWindows.restype = wintypes.BOOL

WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

GWL_STYLE = -16
WS_CAPTION = 0x00C00000
WS_THICKFRAME = 0x00040000


def _get_window_text(hwnd):
    length = _user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return ""
    buf = ctypes.create_unicode_buffer(length + 1)
    _user32.GetWindowTextW(hwnd, buf, length + 1)
    return buf.value


def _get_client_rect(hwnd):
    """Returns the client area (content without borders/titlebar) in screen coordinates."""
    rect = wintypes.RECT()
    _user32.GetClientRect(hwnd, ctypes.byref(rect))
    point = wintypes.POINT(rect.left, rect.top)
    _user32.ClientToScreen(hwnd, ctypes.byref(point))
    return point.x, point.y, rect.right - rect.left, rect.bottom - rect.top


def _is_windowed(hwnd):
    """Check if the window has a title bar / border (= windowed mode)."""
    style = _user32.GetWindowLongW(hwnd, GWL_STYLE)
    return bool(style & WS_CAPTION) or bool(style & WS_THICKFRAME)


def _find_game_windows(title_fragment="Blue Protocol"):
    """Find all visible windows whose title contains the fragment. Pure Win32."""
    results = []

    def _callback(hwnd, _lparam):
        if not _user32.IsWindowVisible(hwnd):
            return True
        title = _get_window_text(hwnd)
        if title_fragment in title:
            x, y, w, h = _get_client_rect(hwnd)
            if w >= 200 and h >= 200:
                results.append((hwnd, title, x, y, w, h))
        return True

    # prevent GC of callback during enumeration
    cb = WNDENUMPROC(_callback)
    _user32.EnumWindows(cb, 0)
    return results


class ScreenConfig:
    def __init__(self):
        self.REFERENCE_WIDTH = 1920
        self.REFERENCE_HEIGHT = 1080
        self.window_title = "Blue Protocol: Star Resonance"
        self.monitor_x = 0
        self.monitor_y = 0
        self.monitor_width = 1920
        self.monitor_height = 1080
        self._detected = False

        self.detect_window()

    def detect_window(self):
        """Detect the game window position and size using Win32 APIs."""
        candidates = _find_game_windows("Blue Protocol")

        for hwnd, title, x, y, w, h in candidates:
            mode = "WINDOWED" if _is_windowed(hwnd) else "FULLSCREEN"
            log(f"[DETECT] candidate: '{title}' client=({x}, {y}) {w}x{h} [{mode}]")

        if not candidates:
            log("⚠️ Game window not found! Make sure the game is running.")
            return False

        # Pick the largest client area
        hwnd, title, x, y, w, h = max(candidates, key=lambda c: c[4] * c[5])
        self.monitor_x = x
        self.monitor_y = y
        self.monitor_width = w
        self.monitor_height = h

        final_mode = "WINDOWED" if _is_windowed(hwnd) else "FULLSCREEN"
        log(f"[{final_mode}] game window detected at ({x}, {y})")
        log(f"[{final_mode}] client area: {w}x{h}")

        self._detected = True
        return True

    def ref_to_screen(self, x, y):
        """Convert 1920x1080 reference coordinates to actual screen coordinates."""
        final_scale_x = self.monitor_width / self.REFERENCE_WIDTH
        final_scale_y = self.monitor_height / self.REFERENCE_HEIGHT
        return (int(x * final_scale_x) + self.monitor_x,
                int(y * final_scale_y) + self.monitor_y)
