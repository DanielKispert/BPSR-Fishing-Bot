"""FishBuddy configuration: loads and validates TOML files with priority merging."""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path
from typing import Dict, List, Optional
import threading

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ImportError:
        raise ImportError("Install tomli for Python <3.11: pip install tomli")

from pydantic import BaseModel, Field, ValidationError, field_validator


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
            raise ValueError(f"bait_type must be 'cheap' or 'special', got: {v!r}")
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
    behavior: BehaviorConfig = Field(default_factory=BehaviorConfig)
    detection: DetectionTomlConfig = Field(default_factory=DetectionTomlConfig)
    screen: ScreenTomlConfig = Field(default_factory=ScreenTomlConfig)
    ocr: OcrConfig = Field(default_factory=OcrConfig)


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _get_user_config_paths() -> List[Path]:
    """Return candidate user-config paths in ascending priority order."""
    paths: List[Path] = []
    if not getattr(sys, "frozen", False):
        # Dev mode: check cwd first (lowest priority)
        paths.append(Path.cwd() / "config.toml")
    if platform.system() == "Windows":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            paths.append(Path(local_app_data) / "FishBuddy" / "config.toml")
    if getattr(sys, "frozen", False):
        # Frozen: config next to exe (highest priority for portable mode)
        paths.append(Path(sys.executable).parent / "config.toml")
    return paths


def _load_config() -> AppConfig:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        default_path = Path(sys._MEIPASS) / "config" / "default_config.toml"
    else:
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
        lines = [f"  * {' > '.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()]
        raise SystemExit("Configuration Error:\n" + "\n".join(lines) + "\nCheck your config.toml.") from exc


_config_lock = threading.Lock()
_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Return the validated AppConfig singleton (loaded lazily)."""
    global _config_instance
    if _config_instance is None:
        with _config_lock:
            if _config_instance is None:  # double-check
                _config_instance = _load_config()
    return _config_instance


def reset_config() -> None:
    """Force config reload on next get_config() call."""
    global _config_instance
    _config_instance = None
