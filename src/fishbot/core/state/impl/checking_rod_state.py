from ..bot_state import BotState
from ..state_type import StateType
from src.fishbot.config.detection_config import ROD_TEMPLATES


class CheckingRodState(BotState):

    MAX_RETRIES = 3
    RETRY_DELAY = 1.5

    def handle(self, screen):
        self.bot.log("[CHECKING_ROD] Checking rod...")
        if self.bot.sleep_or_stop(1):
            return StateType.CHECKING_ROD

        # Capture fresh screen - the one passed in may be stale from state transition
        screen = self.detector.capture_screen()

        found_rod = self._detect_any_rod(screen)

        if not found_rod:
            # Fast-path: detect the "Add a pole" empty slot
            if self._detect_no_rod(screen):
                self.bot.log("[CHECKING_ROD] ⚠️  No rod equipped! Adding...")
                self.bot.stats.increment('rod_breaks')
                return self._replace_rod()

            # Retry with fresh captures if no rod found (fishing UI may still be loading)
            for attempt in range(1, self.MAX_RETRIES + 1):
                if self.bot.is_stopped():
                    return StateType.CHECKING_ROD
                self.bot.log(f"[CHECKING_ROD] Rod not detected (attempt {attempt}/{self.MAX_RETRIES}), retrying...")
                if self.bot.sleep_or_stop(self.RETRY_DELAY):
                    return StateType.CHECKING_ROD
                screen = self.detector.capture_screen()
                found_rod = self._detect_any_rod(screen)
                if found_rod:
                    break

        if not found_rod:
            self.bot.log("[CHECKING_ROD] ⚠️  Rod undetectable after retries. Replacing...")
            return self._replace_rod()

        if self.bot.sleep_or_stop(1):
            return StateType.CHECKING_ROD
        self.bot.log("[CHECKING_ROD] ✅ Rod OK")
        return StateType.CASTING_BAIT

    def _replace_rod(self):
        """Equip a rod via the M-menu. If no rod available, trigger auto-buy."""
        if self.bot.sleep_or_stop(1):
            return StateType.CHECKING_ROD

        self.controller.press_key('m')
        if self.bot.sleep_or_stop(1):
            return StateType.CHECKING_ROD

        x, y = self.window.ref_to_screen(1650, 630)

        if self.controller.click_at_reliable(x, y, self.bot):
            return StateType.CHECKING_ROD
        if self.bot.sleep_or_stop(1):
            return StateType.CHECKING_ROD

        # Close menu
        self.controller.press_key('m')
        if self.bot.sleep_or_stop(0.5):
            return StateType.CHECKING_ROD

        # Verify rod was equipped
        screen = self.detector.capture_screen()
        if self._detect_any_rod(screen):
            self.bot.log("[CHECKING_ROD] ✅ Rod equipped")
            return StateType.CASTING_BAIT

        # Rod equip failed — inventory might be empty
        if self.bot.config.bot.auto_buy_enabled:
            self.bot.log("[CHECKING_ROD] ⚠️ No rod in inventory! Triggering auto-buy...")
            buying_state = self.bot.state_machine.states[StateType.BUYING]
            buying_state.set_buy_target("rod")
            return StateType.BUYING
        else:
            self.bot.log("[CHECKING_ROD] ⚠️ No rod available and auto-buy disabled!")
            self.bot.log("[CHECKING_ROD] ✅ Rod equipped (assuming click worked)")
            return StateType.CASTING_BAIT

    def _detect_any_rod(self, screen):
        """Check all rod templates. Returns True if any rod is detected."""
        rod_templates = ROD_TEMPLATES
        for rod in rod_templates:
            if self.detector.find(screen, rod, 5, debug=self.bot.debug_mode):
                return True
        return False

    def _detect_no_rod(self, screen):
        """Detect the empty rod slot ('Add a pole' button)."""
        return self.detector.find(screen, "no_rod", 3, debug=self.bot.debug_mode) is not None
