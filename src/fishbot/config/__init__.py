# DEPRECATED: Import directly from src.fishbot.config.config_manager instead.
# This module is kept for backward compatibility.

from .bot_config import BotConfig
from .paths import PACKAGE_ROOT, ASSETS_PATH, TEMPLATES_PATH


class Config:

    def __init__(self):
        from .config_manager import get_config
        _app_config = get_config()

        self.bot = BotConfig(_app_config)
        self.ocr = _app_config.ocr

        self.paths = {
            'package_root': PACKAGE_ROOT,
            'assets': ASSETS_PATH,
            'templates': TEMPLATES_PATH
        }

    def get_template_path(self, template_name):
        filename = self.bot.detection.templates.get(template_name)

        if filename:
            return self.paths['templates'] / filename
        return None
