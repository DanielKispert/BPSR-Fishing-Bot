import ctypes

from src.fishbot.utils.logger import log

_AZERTY_LANG_IDS = {0x040C, 0x080C}  # French (France), French (Belgium)


def detect_layout() -> str:
    """Detect the active keyboard layout using the Windows API.

    Returns 'azerty' for French layouts (LANGID 0x040C), 'qwerty' for all others.
    Falls back to 'qwerty' on any error.
    """
    try:
        layout_id = ctypes.windll.user32.GetKeyboardLayout(0) & 0xFFFF
        if layout_id in _AZERTY_LANG_IDS:
            return "azerty"
    except Exception as exc:
        log(f"[KEYS] ⚠️ Layout detection failed ({exc}), defaulting to QWERTY.")
    return "qwerty"


def get_game_keys(layout: str) -> dict:
    """Return key bindings for the given resolved layout.

    layout must be 'azerty' or 'qwerty' (pass the result of detect_layout()
    or the user's explicit override — never 'auto').
    Logs the active layout and the keys that will be used.
    """
    if layout not in ("azerty", "qwerty"):
        raise ValueError(f"get_game_keys: expected 'azerty' or 'qwerty', got {layout!r}")
    if layout == "azerty":
        log("[KEYS] AZERTY detected. Using 'q'/'d' for left/right, ',' for rod selection menu.")
        return {
            "move_left": "q",
            "move_right": "d",
            "equip_menu": ",",
        }
    else:
        log("[KEYS] QWERTY/QWERTZ detected. Using 'a'/'d' for left/right, 'm' for rod selection menu.")
        return {
            "move_left": "a",
            "move_right": "d",
            "equip_menu": "m",
        }
