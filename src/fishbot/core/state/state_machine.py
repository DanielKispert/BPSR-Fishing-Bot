import time

from src.fishbot.utils.logger import log
from .state_type import StateType


class StateMachine:
    def __init__(self, bot):
        self.bot = bot
        self.config = bot.config.bot
        self.states = {}
        self.current_state_name = None
        self.current_state = None
        self.state_start_time = None
        self.last_activity_time = None

    def add_state(self, name, state_instance):
        self.states[name] = state_instance

    def notify_activity(self):
        """Called by states when meaningful activity occurs (e.g. arrow detected, tension read).
        Extends the timeout so active minigames don't get killed."""
        self.last_activity_time = time.time()

    def set_state(self, new_state_name, force=False):
        if not force and new_state_name == self.current_state_name:
            return

        if new_state_name not in self.states:
            log(f"[ERROR] Attempted to switch to unknown state: {new_state_name}")
            return

        if self.current_state_name is None:
            log(f"[INFO] Starting state machine in: {new_state_name.name}")
        elif new_state_name != self.current_state_name:
            log(f"[INFO] Changing state: {self.current_state_name.name} -> {new_state_name.name}")
        elif force:
            log(f"[INFO] Forcing state reset: {new_state_name.name}")

        self.current_state_name = new_state_name
        self.current_state = self.states[self.current_state_name]
        self.current_state.on_enter()
        self.state_start_time = time.time()
        self.last_activity_time = time.time()

        # Adjust screenshot frequency: faster during minigame for debugging
        if new_state_name == StateType.PLAYING_MINIGAME:
            self.bot.detector.screenshot_interval = 0.5
        else:
            self.bot.detector.screenshot_interval = 2.0

    def _check_state_timeout(self):
        timeout_limit = self.config.state_timeouts.get(self.current_state_name)
        if not timeout_limit:
            return False

        elapsed_time = time.time() - self.state_start_time
        since_activity = time.time() - self.last_activity_time
        # Timeout after base limit, but extend if there was recent activity (within 10s)
        if elapsed_time <= timeout_limit or since_activity < 10:
            return False

        log(f"[TIMEOUT] 🚨 State '{self.current_state_name.name}' exceeded {timeout_limit}s (no activity for {since_activity:.0f}s)!")

        self.bot.detector.save_timeout_frame(self.bot.detector.capture_screen(), self.current_state_name.name)
        self.bot.controller.release_all_controls()
        self.bot.stats.increment('timeouts')

        # If we're in the minigame, check for success screen before giving up
        if self.current_state_name == StateType.PLAYING_MINIGAME:
            screen = self.bot.detector.capture_screen()
            if self.bot.detector.find(screen, "success"):
                log("[TIMEOUT] ✅ Success screen detected! Going to FINISHING.")
                if not self.bot.sleep_or_stop(1):
                    self.set_state(StateType.FINISHING, force=True)
            else:
                log("[TIMEOUT] 🔄 No success screen, going to CHECKING_ROD.")
                if not self.bot.sleep_or_stop(2):
                    self.set_state(StateType.CHECKING_ROD, force=True)
        else:
            log("[TIMEOUT] 🚨 Pressing 'ESC' to reset.")
            if not self.bot.is_stopped():
                self.bot.controller.press_key('esc')
            if not self.bot.sleep_or_stop(0.5):
                self.set_state(StateType.STARTING, force=True)

        return True

    def handle(self, screen):
        if self._check_state_timeout():
            return

        new_state_name = self.current_state.handle(screen)
        self.set_state(new_state_name)
