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

        # 1️⃣ Normal case: detect the fishing spot button
        pos = self.detector.find(screen, "fishing_spot_btn", 5, debug=self.bot.debug_mode)

        if pos:
            self.bot.log(f"[STARTING] ✅ Fishing spot detected at {pos}")
            self.bot.log("[STARTING] Pressing 'F'...")
            if self.bot.sleep_or_stop(0.5):
                return StateType.STARTING

            self.controller.press_key('f')
            self.bot.log("[STARTING] Entering fishing mode")
            if self.bot.sleep_or_stop(2):
                return StateType.STARTING

            return StateType.CHECKING_ROD

        # 2️⃣ New: detect if the player is already in fishing mode
        already_fishing = self.detector.find(screen, "level_check", 5, debug=self.bot.debug_mode)

        if already_fishing:
            self.bot.log("[STARTING] 🎣 Already in fishing mode — skipping interaction")
            return StateType.CHECKING_ROD

        # 3️⃣ Fallback: still searching for fishing spot
        current_time = time.time()
        if current_time - self._last_search_log > 2:
            self.bot.log("[STARTING] 🔍 Searching for fishing spot...")

            # wiggle a bit to get the fishing button to come back up
            self.controller.key_down('s')
            self.controller.key_down('d')
            if self.bot.sleep_or_stop(0.1):
                self.controller.key_up('s')
                self.controller.key_up('d')
                return StateType.STARTING
            self.controller.key_up('s')
            self.controller.key_up('d')

            if self.bot.debug_mode:
                self.bot.log("[STARTING] 💡 Debug enabled")
            self._last_search_log = current_time

        return StateType.STARTING
