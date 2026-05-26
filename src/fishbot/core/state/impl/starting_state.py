from ..bot_state import BotState
from ..state_type import StateType

class StartingState(BotState):

    def on_enter(self):
        self.bot.log("[STARTING] 🎣 Starting in fishing UI")

    def handle(self, screen):
        if self.detector.find(screen, "connect_server", 5, debug=self.bot.debug_mode):
            x, y = self.window.ref_to_screen(1100, 795)

            if self.controller.click_at_reliable(x, y, self.bot):
                return StateType.STARTING
            if self.bot.sleep_or_stop(1):
                return StateType.STARTING

            self.bot.log("[RECONNECT] ✅ confirm server connection")
            return StateType.STARTING

        return StateType.CHECKING_ROD
