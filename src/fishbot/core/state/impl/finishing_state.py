from ..bot_state import BotState
from ..state_type import StateType


class FinishingState(BotState):

    def handle(self, screen):

        pos = self.detector.find(screen, "continue", 5, debug=False)

        if pos:
            self.bot.log("[FINISHING] 🖱️ Clicking 'Continue'...")
            if self.controller.click_at_reliable(pos[0], pos[1], self.bot, post_delay=1.0):
                return StateType.FINISHING

            # Count one full fishing attempt
            self.bot.stats.increment("cycles")

            return StateType.CHECKING_ROD

        if self.detector.find(screen, "fishing_spot_btn", 1, debug=False):
            return StateType.STARTING

        return StateType.FINISHING
