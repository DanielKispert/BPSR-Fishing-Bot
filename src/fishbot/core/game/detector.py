import cv2 as cv
import numpy as np

from src.fishbot.utils.logger import log

try:
    import mss
except ImportError:
    log("[ERROR] ❌ MSS library not found! Install with: pip install mss")
    log("[ERROR] The bot cannot run without MSS.")
    exit(1)


class Detector:
    def __init__(self, config):
        self.unified_config = config
        self.detection_config = config.bot.detection
        self.screen_config = config.bot.screen

        self.templates = self._load_templates()
        self.sct = None
        self.monitor = {
            'left': self.screen_config.monitor_x,
            'top': self.screen_config.monitor_y,
            'width': self.screen_config.monitor_width,
            'height': self.screen_config.monitor_height
        }

    def _load_templates(self):
        loaded = {}
        log("[INFO] 📦 Loading templates...")
        for name in self.detection_config.templates:
            path = self.unified_config.get_template_path(name)
            if not (path and path.exists()):
                log(f"[INFO] ❌ {name} - not found at '{path}'")
                continue

            img = cv.imread(str(path), cv.IMREAD_UNCHANGED)
            template_img, mask = None, None

            if img.shape[2] == 4:
                log(f"[INFO] ✅ {name} (with transparency mask)")
                mask = img[:, :, 3]
                template_img = cv.cvtColor(img, cv.COLOR_BGRA2BGR)
            else:
                log(f"[INFO] ✅ {name}")
                template_img = img
            
            loaded[name] = (template_img, mask)
        return loaded
    
    def _generate_concentric_square_pixels(self, center_x, center_y, max_radius):
        """
        Generates x, y pixel coordinates for the perimeters of concentric squares.

        Args:
            center_x (int): The x-coordinate of the center.
            center_y (int): The y-coordinate of the center.
            max_radius (int): The radius of the largest square from the center.

        Yields:
            tuple: (x, y) coordinates for each pixel on the squares.
        """
        # Iterate for each square size, starting from a small radius up to max_radius
        for r in range(1, max_radius + 1):
            # Coordinates for the four sides of the square
            # Top side: x from center_x-r to center_x+r, y fixed at center_y-r
            for x in range(center_x - r, center_x + r + 1):
                yield x, center_y - r
            # Bottom side: x from center_x-r to center_x+r, y fixed at center_y+r
            for x in range(center_x - r, center_x + r + 1):
                yield x, center_y + r
            # Left side: x fixed at center_x-r, y from center_y-r+1 to center_y+r-1
            for y in range(center_y - r + 1, center_y + r):
                yield center_x - r, y
            # Right side: x fixed at center_x+r, y from center_y-r+1 to center_y+r-1
            for y in range(center_y - r + 1, center_y + r):
                yield center_x + r, y

    def capture_screen(self):
        if self.sct is None:
            self.sct = mss.mss()
            log("[INFO] ✅ MSS initialized in bot thread")

        screenshot = self.sct.grab(self.monitor)
        img = np.array(screenshot)
        img = cv.cvtColor(img, cv.COLOR_BGRA2BGR)

        # Scale to reference resolution so ROIs and templates always match
        ref_w = self.screen_config.REFERENCE_WIDTH
        ref_h = self.screen_config.REFERENCE_HEIGHT
        if img.shape[1] != ref_w or img.shape[0] != ref_h:
            img = cv.resize(img, (ref_w, ref_h), interpolation=cv.INTER_LINEAR)

        return img

    def _check_xy(self, search_area, x, y, template_data, template_img, template_name, debug):
        confidence, location = self._perform_match(search_area, template_data)

        if confidence is None:
            return None
        
        precision = self.detection_config.precision
        is_match = confidence >= precision

        if debug and confidence >= .3:
            status = 'MATCH' if is_match else 'NO MATCH'
            log(f"[DEBUG] [{template_name}] at ({x}, {y}) Confidence: {confidence:.2%} (required: {precision:.0%}) -> {status}")

        if is_match:
            return self._calculate_center(location, template_img.shape[:2], (x, y))

        return None

    def _get_search_area(self, screen, template_name, radius, debug):
        template_data = self.templates[template_name]
        template_img, _ = template_data

        roi_config = self.detection_config.rois.get(template_name)
        if isinstance(roi_config, str):
            roi = self.detection_config.rois.get(roi_config)
        else:
            roi = roi_config

        if not roi:
            return screen, (0, 0)

        x, y, w, h = roi
        screen_h, screen_w = screen.shape[:2]
        x = max(0, min(x, screen_w - 1))
        y = max(0, min(y, screen_h - 1))
        w = min(w, screen_w - x)
        h = min(h, screen_h - y)

        if w > 0 and h > 0:
            result = self._check_xy(screen[y:y + h, x:x + w], x, y, template_data, template_img, template_name, debug)

            if result != None:
                return result
            
            if radius > 0:
                concentric_coords = self._generate_concentric_square_pixels(x, y, radius)

                for pixel in list(concentric_coords):
                    x, y = pixel

                    result = self._check_xy(screen[y:y + h, x:x + w], x, y, template_data, template_img, template_name, debug)

                    if result != None:
                        return result

        return None

    def _perform_match(self, search_area, template_data):
        template_img, mask = template_data

        search_gray = cv.cvtColor(search_area, cv.COLOR_BGR2GRAY)
        template_gray = cv.cvtColor(template_img, cv.COLOR_BGR2GRAY)

        if search_gray.shape[0] < template_gray.shape[0] or search_gray.shape[1] < template_gray.shape[1]:
            return None, None

        result = cv.matchTemplate(search_gray, template_gray, cv.TM_CCOEFF_NORMED, mask=mask)
        _, confidence, _, location = cv.minMaxLoc(result)
        return confidence, location

    def _calculate_center(self, location, template_shape, offset):
        h_t, w_t = template_shape
        offset_x, offset_y = offset

        # Position in 1080p reference space (within the game window)
        ref_x = location[0] + w_t // 2 + offset_x
        ref_y = location[1] + h_t // 2 + offset_y

        # Scale back to actual window size, then add window position
        scale_x = self.screen_config.monitor_width / self.screen_config.REFERENCE_WIDTH
        scale_y = self.screen_config.monitor_height / self.screen_config.REFERENCE_HEIGHT
        return (
            int(ref_x * scale_x) + self.screen_config.monitor_x,
            int(ref_y * scale_y) + self.screen_config.monitor_y
        )

    def find(self, screen, template_name, radius = 0, debug=False):
        if template_name not in self.templates:
            log(f"[INFO] ❌ Template '{template_name}' was not loaded.")
            return None
        
        return self._get_search_area(screen, template_name, radius, debug)

        # template_data = self.templates[template_name]
        # template_img, _ = template_data

        # search_area, offset = self._get_search_area(screen, template_name)
        # confidence, location = self._perform_match(search_area, template_data)

        # if confidence is None:
        #     return None

        # precision = self.detection_config.precision
        # is_match = confidence >= precision

        # if debug:
        #     status = 'MATCH' if is_match else 'NO MATCH'
        #     log(f"[DEBUG] [{template_name}] Confidence: {confidence:.2%} (required: {precision:.0%}) -> {status}")

        # if is_match:
        #     return self._calculate_center(location, template_img.shape[:2], offset)

        # return None
