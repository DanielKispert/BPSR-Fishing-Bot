from .paths import TEMPLATES_PATH

class DetectionConfig:
    def __init__(self):

        self.precision = 0.50

        self.templates_path = str(TEMPLATES_PATH)

        self.templates = {
            "fishing_spot_btn": "fishing_spot_btn.png",
            "broken_rod": "broken_rod.png",
            "new_rod": "new_rod.png",
            "reg_rod": "reg_pole.png",
            "sturdy_rod": "sturdy_pole.png",
            "flex_rod": "flex_pole.png",
            "no_rod": "no_rod.png",
            "exclamation": "exclamation.png",
            "left_arrow": "left_arrow.png",
            "right_arrow": "right_arrow.png",
            "failure": "fish_escaped.png",
            "success": "success.png",
            "continue": "continue.png",
            "level_check": "level_check.png",
            "connect_server": "connect.png"
        }

        # General Resolutions Config, But Slow Response Time
        # self.rois = {
        #     "fishing_spot": None,
        #     "broken_rod": None,
        #     "new_rod": None,
        #     "exclamation": None,
        #     "left_arrow": None,
        #     "right_arrow": None,
        #     "success": None,
        #     "continue": None,
        #     "level_check": None
        # }

        #FullHD 1080p Config
        self.rois = {
            "fishing_spot_btn": (1400, 540, 121, 55),
            "broken_rod": (1635, 982, 250, 63),
            "reg_rod": (1598, 970, 290, 63),
            "sturdy_rod": (1597, 969, 274, 67),
            "flex_rod": (1597, 969, 284, 66),
            "no_rod": (1536, 978, 352, 70),
            "new_rod": (1624, 563, 185, 65),
            "exclamation": (929, 438, 52, 142),
            "left_arrow": (740, 490, 220, 100),
            "right_arrow": (960, 490, 220, 100),
            "failure": (973, 630, 702, 101),
            "success": (1422, 924, 337, 106),
            "continue": (1422, 924, 337, 106),
            "level_check": (1101, 985, 48, 29),
            "connect_server": (1057, 763, 279, 67),
        }
