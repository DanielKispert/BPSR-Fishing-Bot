import time

from ..bot_state import BotState
from ..state_type import StateType


class PlayingMinigameState(BotState):

    IDLE_CHECK_DELAY = 8  # Only check for idle UI after this many seconds

    def __init__(self, bot):
        super().__init__(bot)
        self._current_direction = None
        self._minigame_start = None
        self._retry_until = None

    def _handle_arrow(self, direction, screen):
        arrow_template = f"{direction}_arrow"
        key_to_press = 'a' if direction == 'left' else 'd'
        key_to_release = 'd' if direction == 'left' else 'a'
        opposite_direction = 'right' if direction == 'left' else 'left'

        arrow_found = self.detector.find(screen, arrow_template, debug=True)
        if arrow_found:
            if self._current_direction is None:
                self.bot.log(f"[MINIGAME] ▶️ Moving to the {direction} (Holding '{key_to_press}')")
                self.controller.key_down(key_to_press)
                self._current_direction = direction

            if self._current_direction == opposite_direction:
                self.bot.log(f"[MINIGAME] ◀️ Switching to the {direction} (Releasing '{key_to_release}')")
                self.controller.key_up(key_to_release)
                self._current_direction = None

    def _detect_fishing_idle(self, screen):
        """Check if the fishing idle UI is visible.
        Uses level_check (always present in fishing HUD) as primary indicator,
        with rod templates as secondary confirmation."""
        if self.detector.find(screen, "level_check", 5):
            return True
        for rod in ["flex_rod", "sturdy_rod", "reg_rod"]:
            if self.detector.find(screen, rod, 5):
                return True
        return False

    def handle(self, screen):
        now = time.time()
        if self._minigame_start is None or (now - self._minigame_start) > 45:
            self._minigame_start = now

        # Non-blocking retry wait — loop keeps running (screenshots, stop-check)
        if self._retry_until is not None:
            if now < self._retry_until:
                return StateType.PLAYING_MINIGAME
            self._retry_until = None
            return StateType.CHECKING_ROD

        fish_complete = 0
        failed = 0

        if self.detector.find(screen, "success", 1, debug=True):
            fish_complete = 1
            self.bot.log("[MINIGAME] 🐟 Fish caught!")
            self.bot.stats.increment('fish_caught')

        if fish_complete == 0 and self.detector.find(screen, "failure", 1, debug=True):
            fish_complete = 1
            failed = 1
            self.bot.log("[MINIGAME] ❌ Fish escaped!")
            self.bot.stats.increment('fish_escaped')

        if fish_complete == 0:
            elapsed = now - self._minigame_start
            if elapsed > self.IDLE_CHECK_DELAY:
                if self._detect_fishing_idle(screen):
                    fish_complete = 1
                    failed = 1
                    self.bot.log("[MINIGAME] ❌ Fish escaped (idle UI detected)")
                    self.bot.stats.increment('fish_escaped')

        if fish_complete == 1:
            self.controller.release_all_controls()
            self._current_direction = None
            self._minigame_start = None

            if failed == 0:
                if self.config.quick_finish_enabled:
                    self.bot.log("[MINIGAME] ⏩ Quick finishing...")
                    self.controller.press_key('esc')
                    time.sleep(0.5)
                    return StateType.STARTING
                else:
                    return StateType.FINISHING
            else:
                self.bot.log("[MINIGAME] 🔄 Retrying...")
                self._retry_until = now + 2.0
                return StateType.PLAYING_MINIGAME

        self._handle_arrow('left', screen)
        self._handle_arrow('right', screen)

        return StateType.PLAYING_MINIGAME
