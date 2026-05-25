"""FishBuddy Configuration Manager
================================
Loads and validates bot configuration from TOML files.

Config priority (later sources override earlier ones):
  1. src/fishbot/config/default_config.toml  — bundled defaults (always loaded)
  2. %LOCALAPPDATA%\\FishBuddy\\config.toml   — Windows user config
  3. ./config.toml                            — portable mode (highest priority)

Only the keys present in your config file are changed.
All other settings keep their defaults automatically.

─────────────────────────────────────────────────────────────────────────────
NOTE: bot_config.py, detection_config.py, and screen_config.py are deprecated
      thin wrappers around this module. New code should use get_config().
─────────────────────────────────────────────────────────────────────────────
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        raise ImportError(
            "TOML support is not available.\n"
            "If you are using Python 3.9 or 3.10, install the 'tomli' package:\n"
            "  pip install tomli"
        )

from pydantic import BaseModel, Field, ValidationError, field_validator


# ──────────────────────────────────────────────────────────
# Pydantic models — one per TOML section
# ──────────────────────────────────────────────────────────

class HotkeysConfig(BaseModel):
    start_stop: str = "f9"
    pause: str = "f10"
    emergency_stop: str = "f11"


class StateTimeoutsConfig(BaseModel):
    starting: int = 10
    checking_rod: int = 15
    casting_bait: int = 15
    waiting_for_bite: int = 25
    playing_minigame: int = 65
    finishing: int = 10
    buying: int = 30


class AutoBuyConfig(BaseModel):
    enabled: bool = False
    quantity: int = 20
    bait_type: str = "cheap"

    @field_validator("bait_type")
    @classmethod
    def _validate_bait_type(cls, v: str) -> str:
        if v not in ("cheap", "special"):
            raise ValueError(
                f"bait_type must be 'cheap' or 'special', got: {v!r}"
            )
        return v


class BehaviorConfig(BaseModel):
    anti_detection: bool = True
    mouse_jitter: int = 3
    delay_variance: float = 0.2
    casting_delay_variance: float = 0.15
    casting_delay: float = 0.5
    quick_finish_enabled: bool = False
    debug_mode: bool = False
    target_fps: int = 0
    state_timeouts: StateTimeoutsConfig = Field(default_factory=StateTimeoutsConfig)
    auto_buy: AutoBuyConfig = Field(default_factory=AutoBuyConfig)


class DetectionTomlConfig(BaseModel):
    precision: float = 0.65
    precision_overrides: Dict[str, float] = Field(default_factory=dict)
    templates: Dict[str, str] = Field(default_factory=dict)
    color_match_templates: Dict[str, List[int]] = Field(default_factory=dict)
    rois: Dict[str, List[int]] = Field(default_factory=dict)


class WindowedOffsetsConfig(BaseModel):
    top: int = 32
    left: int = 8
    width: int = 16
    height: int = 39


class ScreenTomlConfig(BaseModel):
    game_window_title: str = "Blue Protocol: Star Resonance"
    reference_width: int = 1920
    reference_height: int = 1080
    windowed_offsets: WindowedOffsetsConfig = Field(default_factory=WindowedOffsetsConfig)


class OcrConfig(BaseModel):
    enabled: bool = True
    tesseract_path: str = "auto"


class AppConfig(BaseModel):
    hotkeys: HotkeysConfig = Field(default_factory=HotkeysConfig)
    behavior: BehaviorConfig = Field(default_factory=BehaviorConfig)
    detection: DetectionTomlConfig = Field(default_factory=DetectionTomlConfig)
    screen: ScreenTomlConfig = Field(default_factory=ScreenTomlConfig)
    ocr: OcrConfig = Field(default_factory=OcrConfig)


# ──────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────

def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*, returning a new dict."""
    result = base.copy()
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _get_user_config_paths() -> List[Path]:
    """Return candidate user-config paths in ascending priority order."""
    paths: List[Path] = []

    # Windows installed location (%LOCALAPPDATA%\FishBuddy\config.toml)
    if platform.system() == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            paths.append(Path(local_app_data) / "FishBuddy" / "config.toml")

    # PyInstaller frozen build — sibling of the executable
    if getattr(sys, "frozen", False):
        paths.append(Path(sys.executable).parent / "config.toml")

    # Portable / development — current working directory (highest priority)
    paths.append(Path.cwd() / "config.toml")

    return paths


def _load_config() -> AppConfig:
    default_path = Path(__file__).parent / "default_config.toml"

    with open(default_path, "rb") as fh:
        merged: dict = tomllib.load(fh)

    for user_path in _get_user_config_paths():
        if user_path.exists():
            with open(user_path, "rb") as fh:
                user_data = tomllib.load(fh)
            merged = _deep_merge(merged, user_data)

    try:
        return AppConfig.model_validate(merged)
    except ValidationError as exc:
        lines = []
        for err in exc.errors():
            loc = " > ".join(str(p) for p in err["loc"])
            lines.append(f"  * {loc}: {err['msg']}")
        detail = "\n".join(lines)
        raise SystemExit(
            f"\n❌  Configuration Error\n"
            f"{'─' * 50}\n"
            f"{detail}\n"
            f"{'─' * 50}\n"
            f"Please check your config.toml.\n"
            f"The default settings are documented in:\n"
            f"  {default_path}\n"
        ) from exc


# ──────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────

_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Return the validated AppConfig singleton (loaded lazily on first call)."""
    global _config_instance
    if _config_instance is None:
        _config_instance = _load_config()
    return _config_instance


def reset_config() -> None:
    """Force a config reload on the next get_config() call.

    Mainly useful for tests and hot-reload scenarios.
    """
    global _config_instance
    _config_instance = None
