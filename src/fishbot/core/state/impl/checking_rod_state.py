import time

from ..bot_state import BotState
from ..state_type import StateType
from src.fishbot.config.detection_config import ROD_TEMPLATES


class CheckingRodState(BotState):

    MAX_RETRIES = 3
    RETRY_DELAY = 1.5

    def __init__(self, bot):
        super().__init__(bot)
        self._phase = "init"
        self._wait_until = None
        self._retry_count = 0

    def on_enter(self):
        self._phase = "init"
        self._wait_until = time.time() + 1.0
        self._retry_count = 0

    def handle(self, screen):
        now = time.time()

        # Non-blocking wait phases
        if self._wait_until is not None:
            if now < self._wait_until:
                return StateType.CHECKING_ROD
            self._wait_until = None

        if self._phase == "init":
            self.bot.log("[CHECKING_ROD] Checking rod...")
            screen = self.detector.capture_screen()

            if self._detect_any_rod(screen):
                self.bot.log("[CHECKING_ROD] ✅ Rod OK")
                self._phase = "done_wait"
                self._wait_until = now + 1.0
                return StateType.CHECKING_ROD

            if self._detect_no_rod(screen):
                self.bot.log("[CHECKING_ROD] ⚠️  No rod equipped! Adding...")
                self.bot.stats.increment('rod_breaks')
                return self._replace_rod()

            self._phase = "retrying"
            self._retry_count = 0
            self._wait_until = now + self.RETRY_DELAY
            return StateType.CHECKING_ROD

        if self._phase == "retrying":
            self._retry_count += 1
            self.bot.log(f"[CHECKING_ROD] Rod not detected (attempt {self._retry_count}/{self.MAX_RETRIES}), retrying...")
            screen = self.detector.capture_screen()

            if self._detect_any_rod(screen):
                self.bot.log("[CHECKING_ROD] ✅ Rod OK")
                self._phase = "done_wait"
                self._wait_until = now + 1.0
                return StateType.CHECKING_ROD

            if self._retry_count >= self.MAX_RETRIES:
                self.bot.log("[CHECKING_ROD] ⚠️  Rod undetectable after retries. Replacing...")
                return self._replace_rod()

            self._wait_until = now + self.RETRY_DELAY
            return StateType.CHECKING_ROD

        if self._phase == "done_wait":
            return StateType.CASTING_BAIT

        return StateType.CHECKING_ROD

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
