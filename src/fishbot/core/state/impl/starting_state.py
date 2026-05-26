import time

from ..bot_state import BotState
from ..state_type import StateType

class StartingState(BotState):

    def __init__(self, bot):
        super().__init__(bot)
        self._last_search_log = 0

    def on_enter(self):
        self._last_search_log = 0

    def handle(self, screen):
        if self.detector.find(screen, "connect_server", 5, debug=self.bot.debug_mode):
            x, y = self.window.ref_to_screen(1100, 795)

            if self.controller.click_at_reliable(x, y, self.bot):
                return StateType.STARTING
            if self.bot.sleep_or_stop(1):
                return StateType.STARTING

            self.bot.log("[RECONNECT] ✅ confirm server connection")

        # Detect if the player is already in fishing mode
        if self.detector.find(screen, "level_check", 5, debug=self.bot.debug_mode):
            self.bot.log("[STARTING] 🎣 Fishing UI detected")
            return StateType.CHECKING_ROD

        # Still waiting for fishing UI
        current_time = time.time()
        if current_time - self._last_search_log > 5:
            self.bot.log("[STARTING] ⏳ Waiting for fishing UI... (open fishing mode first)")
            self._last_search_log = current_time

        return StateType.STARTING
