import time

from ..bot_state import BotState
from ..state_type import StateType


class CheckingRodState(BotState):

    MAX_RETRIES = 3
    RETRY_DELAY = 1.5

    def handle(self, screen):
        self.bot.log("[CHECKING_ROD] Checking rod...")
        time.sleep(1)

        # Capture fresh screen - the one passed in may be stale from state transition
        screen = self.detector.capture_screen()

        found_rod = self._detect_any_rod(screen)

        # Retry with fresh captures if no rod found (fishing UI may still be loading)
        if not found_rod:
            for attempt in range(1, self.MAX_RETRIES + 1):
                self.bot.log(f"[CHECKING_ROD] Rod not detected (attempt {attempt}/{self.MAX_RETRIES}), retrying...")
                time.sleep(self.RETRY_DELAY)
                screen = self.detector.capture_screen()
                found_rod = self._detect_any_rod(screen)
                if found_rod:
                    break

        if not found_rod:
            self.bot.log("[CHECKING_ROD] ⚠️  Broken rod! Replacing...")
            self.bot.stats.increment('rod_breaks')
            time.sleep(1)

            self.controller.press_key('m')
            time.sleep(1)

            x, y = self.window.ref_to_screen(1650, 580)

            self.controller.move_to(x, y)
            time.sleep(0.5)
            self.controller.move_to(x, y)
            time.sleep(0.5)
            self.controller.click('left')
            time.sleep(1)

            self.bot.log("[CHECKING_ROD] ✅ Rod replaced")
        else:
            time.sleep(1)
            self.bot.log("[CHECKING_ROD] ✅ Rod OK")

        return StateType.CASTING_BAIT

    def _detect_any_rod(self, screen):
        """Check all rod templates. Returns True if any rod is detected."""
        rod_templates = ["flex_rod", "sturdy_rod", "reg_rod"]
        for rod in rod_templates:
            if self.detector.find(screen, rod, 5, debug=self.bot.debug_mode):
                return True
        return False
