import random

from ..bot_state import BotState
from ..state_type import StateType


class CastingBaitState(BotState):

    def handle(self, screen):
        # Check if bait slot is empty (auto-buy trigger)
        if self.bot.config.bot.auto_buy_enabled:
            if "empty_bait_slot" in self.detector.templates:
                if self.detector.find(screen, "empty_bait_slot", 3):
                    self.bot.log("[CASTING_BAIT] ⚠️ Bait depleted! Triggering auto-buy...")
                    buying_state = self.bot.state_machine.states[StateType.BUYING]
                    buying_state.set_buy_target("bait")
                    return StateType.BUYING

        base_delay = self.config.casting_delay
        if self.bot.config.bot.anti_detection:
            variance = self.bot.config.bot.casting_delay_variance
            factor = 1.0 + random.uniform(-variance, variance)
            delay = base_delay * factor
        else:
            delay = base_delay
        self.bot.log(f"[CASTING_BAIT] 🎣 Waiting {delay:.2f} seconds...")
        if self.bot.sleep_or_stop(delay):
            return StateType.CASTING_BAIT

        center_x = self.config.screen.monitor_width // 2 + self.config.screen.monitor_x
        center_y = self.config.screen.monitor_height // 2 + self.config.screen.monitor_y

        self.bot.log(f"[CASTING_BAIT] 📍 Moving mouse to center of the screen ({center_x}, {center_y})")
        self.controller.move_to(center_x, center_y)
        if self.bot.sleep_or_stop(1):
            return StateType.CASTING_BAIT

        self.bot.log("[CASTING_BAIT] 🖱️ Clicking to ensure focus...")
        self.controller.click_at(center_x, center_y)
        if self.bot.sleep_or_stop(0.5):
            return StateType.CASTING_BAIT

        self.bot.log("[CASTING_BAIT] 🎣 Casting bait...")
        self.controller.mouse_down('left')
        if self.bot.sleep_or_stop(0.1):
            self.controller.mouse_up('left')
            return StateType.CASTING_BAIT
        self.controller.mouse_up('left')
        if self.bot.sleep_or_stop(2):
            return StateType.CASTING_BAIT

        return StateType.WAITING_FOR_BITE
