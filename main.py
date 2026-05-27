import ctypes
# DPI awareness must be set before any window/screen APIs are called
ctypes.windll.shcore.SetProcessDpiAwareness(2)

from src.fishbot.core.fishing_bot import FishingBot
from src.fishbot.core.game.hotkeys import Hotkeys
from src.fishbot.utils.logger import log


def main():
    bot = FishingBot()

    hotkeys = Hotkeys(bot)

    bot.start()

    log("[INFO] Hotkeys: F6=start, F9=start+debug, F7=pause, F8=emergency stop, "
        "F10=burst screenshots, F11=region+ROI overlay.")

    try:
        while not bot.is_stopped():
            if not hotkeys.paused:
                bot.update()

            bot.sleep_or_stop(0.05)
    finally:
        hotkeys.shutdown()

    log("[INFO] Bot finished.")


if __name__ == "__main__":
    main()
