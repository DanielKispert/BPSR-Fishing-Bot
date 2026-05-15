from abc import ABC, abstractmethod

from ..bot_component import BotComponent


class BotState(BotComponent, ABC):

    def __init__(self, bot):
        super().__init__(bot)
        self.window = bot.config.bot.screen

    @abstractmethod
    def handle(self, screen):
        pass

    def on_enter(self):
        """Called when the state machine transitions INTO this state. Override to reset state."""
        pass
