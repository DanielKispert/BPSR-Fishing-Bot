import threading
import time

from src.fishbot.config import Config
from src.fishbot.core.game.controller import GameController
from src.fishbot.core.game.detector import Detector
from src.fishbot.core.state.impl.casting_bait_state import CastingBaitState
from src.fishbot.core.state.impl.checking_rod_state import CheckingRodState
from src.fishbot.core.state.impl.finishing_state import FinishingState
from src.fishbot.core.state.impl.playing_minigame_state import PlayingMinigameState
from src.fishbot.core.state.impl.starting_state import StartingState
from src.fishbot.core.state.impl.waiting_for_bite_state import WaitingForBiteState
from src.fishbot.core.state.impl.buying_state import BuyingState
from src.fishbot.core.state.state_machine import StateMachine
from src.fishbot.core.state.state_type import StateType
from src.fishbot.core.stats import StatsTracker
from src.fishbot.utils.logger import log
from src.fishbot.config.config_manager import get_config
from src.fishbot.utils.keyboard_layout import detect_layout, get_game_keys

class FishingBot:
    def __init__(self):
        self.config = Config()
        self.stats = StatsTracker()
        self.log = log

        layout_setting = get_config().keys.layout
        resolved_layout = detect_layout() if layout_setting == "auto" else layout_setting
        game_keys = get_game_keys(resolved_layout)

        self.detector = Detector(self.config)
        self.controller = GameController(self.config, game_keys)
        self.state_machine = StateMachine(self)

        self._stopped = False
        self._stop_event = threading.Event()
        self.debug_mode = self.config.bot.debug_mode
        self._stats_shown = False

        self.target_delay = 0
        if self.config.bot.target_fps > 0:
            self.target_delay = 1.0 / self.config.bot.target_fps

        self._register_states()

    def _register_states(self):
        self.state_machine.add_state(StateType.STARTING, StartingState(self))
        self.state_machine.add_state(StateType.CHECKING_ROD, CheckingRodState(self))
        self.state_machine.add_state(StateType.CASTING_BAIT, CastingBaitState(self))
        self.state_machine.add_state(StateType.WAITING_FOR_BITE, WaitingForBiteState(self))
        self.state_machine.add_state(StateType.PLAYING_MINIGAME, PlayingMinigameState(self))
        self.state_machine.add_state(StateType.FINISHING, FinishingState(self))
        self.state_machine.add_state(StateType.BUYING, BuyingState(self))

    def start(self):
        self._stopped = False
        self._stop_event.clear()
        self._stats_shown = False

        log("[INFO] 🎣 Bot ready!")
        log("[INFO] ⚠️ IMPORTANT: Keep the game in FOCUS (active window)")
        log(f"[INFO] ⚙️ Accuracy: {self.config.bot.detection.precision * 100:.0f}%")
        log(f"[INFO] ⚙️ Target FPS: {'MAX' if self.config.bot.target_fps == 0 else self.config.bot.target_fps}")

        log("[INFO] ⚠️ Warming up detection system...")
        self.sleep_or_stop(1)
        self.state_machine.set_state(StateType.STARTING)

    def update(self):
        if self._stopped:
            return

        loop_start = time.time()

        screen = self.detector.capture_screen()

        if self._stopped:
            return

        self.state_machine.handle(screen)

        if self.target_delay > 0:
            loop_time = time.time() - loop_start
            sleep_time = max(0, self.target_delay - loop_time)
            if sleep_time > 0:
                self.sleep_or_stop(sleep_time)

    def stop(self):
        # Always show stats once
        if not self._stats_shown:
            self.stats.show()
            self._stats_shown = True

        # Proceed with shutdown only once
        if not self._stopped:
            self.log("[BOT] 🛑 Shutting down the bot...")
            self._stopped = True
            self._stop_event.set()

            try:
                self.controller.release_all_controls()
            except Exception as e:
                self.log(f"[ERROR] Failed to release controls: {e}")

    def sleep_or_stop(self, seconds: float) -> bool:
        """Sleep for the given duration or return early if stop is requested.
        Returns True if the bot was stopped during the wait, False otherwise."""
        return self._stop_event.wait(timeout=seconds)

    def is_stopped(self):
        return self._stopped
