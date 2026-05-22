import random
import time


from ..bot_state import BotState
from ..state_type import StateType
from src.fishbot.config.detection_config import ROD_TEMPLATES



class PlayingMinigameState(BotState):

    IDLE_CHECK_DELAY = 20  # Only check for idle UI after this many seconds
    TENSION_THRESHOLD = 80  # Release mouse when tension exceeds this percentage
    TENSION_CHECK_INTERVAL = 2  # OCR every 2nd frame for performance

    def __init__(self, bot):
        super().__init__(bot)
        self._current_direction = None
        self._minigame_start = None
        self._retry_until = None
        self._tension_release_until = None
        self._frame_counter = 0

    def on_enter(self):
        self._current_direction = None
        self._minigame_start = None
        self._retry_until = None
        self._tension_release_until = None
        self._frame_counter = 0

    def _handle_arrow(self, direction, screen):
        arrow_template = f"{direction}_arrow"
        key_to_press = 'a' if direction == 'left' else 'd'
        key_to_release = 'd' if direction == 'left' else 'a'

        arrow_found = self.detector.find(screen, arrow_template, debug=True)
        if not arrow_found:
            return False

        if self._current_direction == direction:
            # Already holding the correct key
            return True

        if self._current_direction is not None:
            # Switch: release old key first
            self.bot.log(f"[MINIGAME]  Switching to {direction} ('{key_to_release}' → '{key_to_press}')")
            self.controller.key_up(key_to_release)
            # Micro-pause between key release and press (human-like)
            if self.bot.config.bot.anti_detection:
                time.sleep(random.uniform(0.02, 0.06))
        else:
            self.bot.log(f"[MINIGAME] ▶️ Moving {direction} (Holding '{key_to_press}')")

        self.controller.key_down(key_to_press)
        self._current_direction = direction
        return True

    def _detect_fishing_idle(self, screen):
        """Check if the fishing idle UI is visible.
        Requires BOTH level_check AND a rod template to match (reduces false positives)."""
        if not self.detector.find(screen, "level_check"):
            return False
        for rod in ROD_TEMPLATES:
            if self.detector.find(screen, rod):
                return True
        return False

    def handle(self, screen):
        now = time.time()
        if self._minigame_start is None:
            self._minigame_start = now

        self._frame_counter += 1

        # Non-blocking retry wait — loop keeps running (screenshots, stop-check)
        if self._retry_until is not None:
            if now < self._retry_until:
                return StateType.PLAYING_MINIGAME
            self._retry_until = None
            return StateType.CHECKING_ROD

        fish_complete = False
        failed = False

        if self.detector.find(screen, "success", debug=True):
            fish_complete = True
            self.bot.log("[MINIGAME]  Fish caught!")
            self.bot.stats.increment('fish_caught')

        # failure detection skipped for performance (~74ms saved per frame)
        # idle check after 20s catches escaped fish reliably

        if not fish_complete:
            elapsed = now - self._minigame_start
            if elapsed > self.IDLE_CHECK_DELAY:
                if self._detect_fishing_idle(screen):
                    fish_complete = True
                    failed = True
                    self.bot.log('[MINIGAME] ❌ Fish escaped (idle UI detected)')
                    self.bot.stats.increment('fish_escaped')

        if fish_complete:
            self.controller.release_all_controls()
            self._current_direction = None
            self._minigame_start = None

            if not failed:
                if self.config.quick_finish_enabled:
                    self.bot.log("[MINIGAME] ⏩ Quick finishing...")
                    self.controller.press_key('esc')
                    if self.bot.sleep_or_stop(0.5):
                        return StateType.PLAYING_MINIGAME
                    return StateType.STARTING
                else:
                    return StateType.FINISHING
            else:
                self.bot.log("[MINIGAME]  Retrying...")
                self._retry_until = now + 2.0
                return StateType.PLAYING_MINIGAME

        # Try both directions — first match wins
        if not self._handle_arrow('left', screen):
            self._handle_arrow('right', screen)

        # Tension management (non-blocking, OCR every 2nd frame for performance)
        if self._tension_release_until is not None:
            if now < self._tension_release_until:
                pass
            else:
                self.controller.mouse_down('left')
                self._tension_release_until = None
        elif self._frame_counter % self.TENSION_CHECK_INTERVAL == 0:
            tension = self.detector.read_tension_percent(screen)
            if tension is not None and tension >= self.TENSION_THRESHOLD:
                self.bot.log(f"[MINIGAME] ⚠️ Tension {tension}% — releasing mouse")
                self.controller.mouse_up('left')
                self._tension_release_until = now + 1.0

        return StateType.PLAYING_MINIGAME
