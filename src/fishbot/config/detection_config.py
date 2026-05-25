# DEPRECATED: Use src.fishbot.config.config_manager.get_config() instead.
# This file is kept for backward compatibility.
# Settings are now loaded from default_config.toml (and optionally config.toml).

from .paths import TEMPLATES_PATH

# Rod template names — used by state handlers to identify rod types
ROD_TEMPLATES = ("flex_rod", "sturdy_rod", "reg_rod")

_DEFAULT_TEMPLATES = {
    "fishing_spot_btn": "fishing_spot_btn.png",
    "reg_rod": "reg_pole.png",
    "sturdy_rod": "sturdy_pole.png",
    "flex_rod": "flex_pole.png",
    "broken_rod": "broken_rod.png",
    "no_rod": "no_rod.png",
    "exclamation": "exclamation.png",
    "left_arrow": "left_arrow.png",
    "right_arrow": "right_arrow.png",
    "failure": "fish_escaped.png",
    "success": "success.png",
    "continue": "continue.png",
    "level_check": "level_check.png",
    "connect_server": "connect.png",
    "shop_icon": "shop_icon.png",
    "shop_rod_tab": "shop_rod_tab.png",
    "shop_bait_tab": "shop_bait_tab.png",
    "shop_bait_cheap_tab": "shop_bait_cheap_tab.png",
    "shop_quantity": "shop_quantity.png",
    "shop_buy_btn": "shop_buy_btn.png",
    "shop_ok_btn": "shop_ok_btn.png",
    "shop_confirm": "shop_confirm.png",
    "shop_close": "shop_close.png",
    "empty_bait_slot": "empty_bait_slot.png",
}

_DEFAULT_COLOR_MATCH = {
    "left_arrow": (0, 30, 80, 30, 255, 255),
    "right_arrow": (0, 30, 80, 30, 255, 255),
}

_DEFAULT_ROIS = {
    "fishing_spot_btn": (1400, 540, 121, 55),
    "reg_rod": (1598, 970, 290, 63),
    "sturdy_rod": (1597, 969, 274, 67),
    "flex_rod": (1597, 969, 284, 66),
    "broken_rod": (1597, 969, 284, 66),
    "no_rod": (1536, 978, 352, 70),
    "exclamation": (929, 438, 52, 142),
    "left_arrow": (740, 490, 170, 100),
    "right_arrow": (1010, 490, 170, 100),
    "failure": (973, 630, 702, 101),
    "success": (1422, 924, 337, 106),
    "continue": (1422, 924, 337, 106),
    "level_check": (1101, 985, 48, 29),
    "connect_server": (1057, 763, 279, 67),
    "shop_icon": (400, 200, 1120, 680),
    "shop_rod_tab": (400, 200, 600, 400),
    "shop_bait_tab": (400, 200, 600, 400),
    "shop_bait_cheap_tab": (400, 200, 600, 400),
    "shop_quantity": (700, 400, 500, 200),
    "shop_buy_btn": (800, 600, 400, 200),
    "shop_ok_btn": (700, 400, 500, 200),
    "shop_confirm": (700, 400, 500, 300),
    "shop_close": (1200, 150, 200, 100),
    "empty_bait_slot": (1300, 950, 150, 80),
    "tension_bar": (1000, 820, 320, 60),
}


class DetectionConfig:
    def __init__(self, toml_detection=None):
        if toml_detection is not None:
            self._init_from_toml(toml_detection)
        else:
            # Legacy fallback: hardcoded defaults.
            # DEPRECATED — pass a DetectionTomlConfig from config_manager instead.
            self._init_legacy()

    def _init_from_toml(self, cfg):
        """Populate from a validated DetectionTomlConfig (from config_manager)."""
        self.precision = cfg.precision
        self.precision_overrides = dict(cfg.precision_overrides)
        self.color_match_templates = {
            k: tuple(v) for k, v in cfg.color_match_templates.items()
        }
        self.templates_path = str(TEMPLATES_PATH)
        self.templates = dict(cfg.templates)
        self.rois = {k: tuple(v) for k, v in cfg.rois.items()}

    def _init_legacy(self):
        """Hardcoded defaults — only used when no DetectionTomlConfig is provided."""
        self.precision = 0.65
        self.precision_overrides = {}
        self.color_match_templates = dict(_DEFAULT_COLOR_MATCH)
        self.templates_path = str(TEMPLATES_PATH)
        self.templates = dict(_DEFAULT_TEMPLATES)
        self.rois = dict(_DEFAULT_ROIS)
