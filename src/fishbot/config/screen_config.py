# DEPRECATED: Use src.fishbot.config.config_manager.get_config() instead.
# This file is kept for backward compatibility.
# Settings are now loaded from default_config.toml (and optionally config.toml).

import pywinctl as pwc


class ScreenConfig:
    def __init__(self, toml_screen=None):
        if toml_screen is not None:
            self.REFERENCE_WIDTH = toml_screen.reference_width
            self.REFERENCE_HEIGHT = toml_screen.reference_height
            self.window_title = toml_screen.game_window_title
            offsets = toml_screen.windowed_offsets
            _windowed_top = offsets.top
            _windowed_left = offsets.left
            _windowed_width = offsets.width
            _windowed_height = offsets.height
        else:
            # Legacy fallback: hardcoded defaults.
            # DEPRECATED — pass a ScreenTomlConfig from config_manager instead.
            self.REFERENCE_WIDTH = 1920
            self.REFERENCE_HEIGHT = 1080
            self.window_title = "Blue Protocol: Star Resonance"
            _windowed_top = 32
            _windowed_left = 8
            _windowed_width = 16
            _windowed_height = 39

        self.monitor_x = 0
        self.monitor_y = 0
        self.monitor_width = self.REFERENCE_WIDTH
        self.monitor_height = self.REFERENCE_HEIGHT

        windows = pwc.getAllWindows()

        for window in windows:
            if self.window_title in window.title:
                (self.monitor_x, self.monitor_y) = window.topleft
                (self.monitor_width, self.monitor_height) = window.size

                if self.monitor_x > 0 or self.monitor_y > 0:
                    self.monitor_y = self.monitor_y + _windowed_top
                    self.monitor_x = self.monitor_x + _windowed_left
                    self.monitor_width = self.monitor_width - _windowed_width
                    self.monitor_height = self.monitor_height - _windowed_height

                    print(f"game window detected at ({self.monitor_x}, {self.monitor_y})")
                    print(f"width and height ({self.monitor_width}, {self.monitor_height})")
                break
        else:
            print("Window not found. using defaults.")

    def ref_to_screen(self, x, y):
        """Convert 1920x1080 reference coordinates to actual screen coordinates."""
        scale_x = self.monitor_width / self.REFERENCE_WIDTH
        scale_y = self.monitor_height / self.REFERENCE_HEIGHT
        return (int(x * scale_x) + self.monitor_x,
                int(y * scale_y) + self.monitor_y)
