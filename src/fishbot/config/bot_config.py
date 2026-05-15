from .screen_config import ScreenConfig
from .detection_config import DetectionConfig
from src.fishbot.core.state.state_type import StateType

class BotConfig:
    def __init__(self):

        self.screen = ScreenConfig()
        self.detection = DetectionConfig()

        self.state_timeouts = {
            StateType.STARTING: 10,
            StateType.CHECKING_ROD: 15,
            StateType.CASTING_BAIT: 15,
            StateType.WAITING_FOR_BITE: 25,
            StateType.PLAYING_MINIGAME: 30,
            StateType.FINISHING: 10,
            StateType.BUYING: 30,
        }

        # Enable quick finish after the minigame
        self.quick_finish_enabled = False

        self.debug_mode = False

        # Target FPS (frames per second)
        # 0 means unlimited
        self.target_fps = 0

        # Delays (in seconds)
        self.casting_delay = 0.5

        # Anti-detection settings
        self.anti_detection = True  # Master toggle
        self.mouse_jitter = 3       # Max random offset in pixels (±N)
        self.delay_variance = 0.2   # Random variance on delays (±20%)
        self.casting_delay_variance = 0.15  # Random variance on cast timing (±15%)
        
        # Auto-buy settings
        self.auto_buy_enabled = False        # Enable auto-purchase when supplies run out
        self.auto_buy_quantity = 20         # How many to buy at once (rods or bait)
        self.auto_buy_bait_type = "cheap"   # "cheap" or "special"
