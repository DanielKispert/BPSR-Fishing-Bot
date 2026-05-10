import keyboard
import multiprocessing
from src.fishbot.utils.logger import log
from src.fishbot.utils.roi_visualizer import main as show_roi_visualizer

class Hotkeys:
    def __init__(self, bot):
        self.bot = bot
        self.paused = True
        self.visualizer_process = None
        self._register_hotkeys()

    def _register_hotkeys(self):
        keyboard.add_hotkey('6', self._start_debug)
        keyboard.add_hotkey('7', self._start_normal)
        keyboard.add_hotkey('8', self._stop)
        keyboard.add_hotkey('9', self._toggle_visualizer)
        log("[INFO] ✅ Hotkeys registered: '6' (Start+Debug), '7' (Start), '8' (Exit), '9' (ROI Visualizer)")

    def _start_debug(self):
        if self.paused:
            self.bot.debug_mode = True
            self.bot.detector.screenshots_enabled = True
            self.paused = False
            log("[HOTKEY] 🐛 Bot RUNNING (DEBUG MODE - screenshots enabled)")
        else:
            self.paused = True
            log("[HOTKEY] Bot PAUSED.")

    def _start_normal(self):
        if self.paused:
            self.bot.debug_mode = False
            self.bot.detector.screenshots_enabled = False
            self.paused = False
            log("[HOTKEY] Bot RUNNING.")
        else:
            self.paused = True
            log("[HOTKEY] Bot PAUSED.")

    def _stop(self):
        log("[HOTKEY] Stopping the bot...")
        if self.visualizer_process and self.visualizer_process.is_alive():
            self.visualizer_process.terminate()
        self.bot.stop()

    def _toggle_visualizer(self):
        if self.visualizer_process and self.visualizer_process.is_alive():
            log("[HOTKEY] Closing the ROI visualizer.")
            self.visualizer_process.terminate()
            self.visualizer_process = None
        else:
            log("[HOTKEY] Opening the ROI visualizer.")
            self.visualizer_process = multiprocessing.Process(target=show_roi_visualizer, daemon=True)
            self.visualizer_process.start()

    def wait_for_exit(self):
        """Keeps the script running until the exit hotkey is pressed."""
        keyboard.wait('8')
