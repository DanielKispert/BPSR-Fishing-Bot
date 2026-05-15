import random
import time

import pyautogui as auto

from src.fishbot.utils.logger import log


class GameController:
    def __init__(self, config):
        self.config = config.bot
        auto.FAILSAFE = True
        auto.PAUSE = 0.05
        self.anti_detection = config.bot.anti_detection
        self.jitter_range = config.bot.mouse_jitter
        self.delay_variance = config.bot.delay_variance

    def _jitter(self, x, y):
        """Add random pixel offset to coordinates for anti-detection."""
        if not self.anti_detection:
            return x, y
        jitter = self.jitter_range
        return (
            x + random.randint(-jitter, jitter),
            y + random.randint(-jitter, jitter)
        )

    def _vary_delay(self, base_delay):
        """Add random variance to a delay for anti-detection."""
        if not self.anti_detection or base_delay <= 0:
            return base_delay
        variance = self.delay_variance
        factor = 1.0 + random.uniform(-variance, variance)
        return max(0.01, base_delay * factor)

    def press_key(self, key):
        log(f"[CONTROLLER] 🔘 Pressing key: {key}")
        auto.press(key)
        time.sleep(self._vary_delay(0.1))

    def click(self, button='left', clicks=1, interval=0.1):
        log(f"[CONTROLLER] 🖱️ Clicking: {button} ({clicks}x)")
        auto.click(button=button, clicks=clicks, interval=interval)
        time.sleep(self._vary_delay(0.15))

    def click_at(self, x, y, button='left'):
        log(f"[CONTROLLER] 🖱️ Clicking at ({x}, {y})")
        jx, jy = self._jitter(x, y)
        auto.click(jx, jy, button=button)
        time.sleep(self._vary_delay(0.15))

    def move_to(self, x, y):
        log(f"[CONTROLLER] 📍 Moving mouse to: ({x}, {y})")
        jx, jy = self._jitter(x, y)
        auto.moveTo(jx, jy, duration=0.2)
        time.sleep(self._vary_delay(0.1))

    def mouse_down(self, button='left'):
        log(f"[CONTROLLER] 🖱️ ⬇️ Holding mouse: {button}")
        auto.mouseDown(button=button)
        time.sleep(self._vary_delay(0.1))

    def mouse_up(self, button='left'):
        log(f"[CONTROLLER] 🖱️ ⬆️ Releasing mouse: {button}")
        auto.mouseUp(button=button)
        time.sleep(self._vary_delay(0.1))

    def key_down(self, key):
        log(f"[CONTROLLER] 🔘 ⬇️ Holding key: {key}")
        auto.keyDown(key)

    def key_up(self, key):
        log(f"[CONTROLLER] 🔘 ⬆️ Releasing key: {key}")
        auto.keyUp(key)

    def release_all_controls(self):
        log("[CONTROLLER] ⚠️ Releasing all controls...")
        self.mouse_up('left')
        self.mouse_up('right')
        self.key_up('a')
        self.key_up('d')

    def click_at_reliable(self, x, y, bot, pre_delay=0.5, post_delay=0.5):
        """Move to position twice (to ensure landing), then click.
        Uses bot.sleep_or_stop for interruptible delays.
        Returns True if stopped during the operation."""
        self.move_to(x, y)
        if bot.sleep_or_stop(pre_delay):
            return True
        self.move_to(x, y)
        if bot.sleep_or_stop(post_delay):
            return True
        self.click('left')
        return False
