# DEPRECATED: Use src.fishbot.config.config_manager.get_config() instead.
# This file is kept for backward compatibility.
# Settings are now loaded from default_config.toml (and optionally config.toml).

from .screen_config import ScreenConfig
from .detection_config import DetectionConfig
from src.fishbot.core.state.state_type import StateType

# Mapping from TOML timeout keys to StateType enum values
_TIMEOUT_KEY_TO_STATE = {
    "starting": StateType.STARTING,
    "checking_rod": StateType.CHECKING_ROD,
    "casting_bait": StateType.CASTING_BAIT,
    "waiting_for_bite": StateType.WAITING_FOR_BITE,
    "playing_minigame": StateType.PLAYING_MINIGAME,
    "finishing": StateType.FINISHING,
    "buying": StateType.BUYING,
}


class BotConfig:
    def __init__(self, app_config=None):
        if app_config is not None:
            self._init_from_toml(app_config)
        else:
            # Legacy fallback: hardcoded defaults.
            # DEPRECATED — pass an AppConfig from config_manager.get_config() instead.
            self._init_legacy()

    def _init_from_toml(self, app_config):
        """Populate attributes from a validated AppConfig (from config_manager)."""
        self.screen = ScreenConfig(app_config.screen)
        self.detection = DetectionConfig(app_config.detection)

        b = app_config.behavior
        ab = b.auto_buy

        timeouts_raw = b.state_timeouts.model_dump()
        self.state_timeouts = {
            _TIMEOUT_KEY_TO_STATE[k]: v
            for k, v in timeouts_raw.items()
            if k in _TIMEOUT_KEY_TO_STATE
        }

        self.quick_finish_enabled = b.quick_finish_enabled
        self.debug_mode = b.debug_mode
        self.target_fps = b.target_fps
        self.casting_delay = b.casting_delay
        self.anti_detection = b.anti_detection
        self.mouse_jitter = b.mouse_jitter
        self.delay_variance = b.delay_variance
        self.casting_delay_variance = b.casting_delay_variance
        self.auto_buy_enabled = ab.enabled
        self.auto_buy_quantity = ab.quantity
        self.auto_buy_bait_type = ab.bait_type

    def _init_legacy(self):
        """Hardcoded defaults — only used when no AppConfig is provided."""
        self.screen = ScreenConfig()
        self.detection = DetectionConfig()

        self.state_timeouts = {
            StateType.STARTING: 10,
            StateType.CHECKING_ROD: 15,
            StateType.CASTING_BAIT: 15,
            StateType.WAITING_FOR_BITE: 25,
            StateType.PLAYING_MINIGAME: 30,
            StateType.FINISHING: 10,
            StateType.BUYING: 30,
        }

        self.quick_finish_enabled = False
        self.debug_mode = False
        self.target_fps = 0
        self.casting_delay = 0.5
        self.anti_detection = True
        self.mouse_jitter = 3
        self.delay_variance = 0.2
        self.casting_delay_variance = 0.15
        self.auto_buy_enabled = False
        self.auto_buy_quantity = 20
        self.auto_buy_bait_type = "cheap"
