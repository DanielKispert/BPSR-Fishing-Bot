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
    REFERENCE_WIDTH = 1920
    REFERENCE_HEIGHT = 1080

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

        # Scale factors computed on first capture (actual pixels vs reference)
        self._scale_x = None
        self._scale_y = None
        self._actual_width = None
        self._actual_height = None

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

    def capture_screen(self):
        if self.sct is None:
            self.sct = mss.mss()
            log("[INFO] ✅ MSS initialized in bot thread")

        screenshot = self.sct.grab(self.monitor)
        img = np.array(screenshot)
        img = cv.cvtColor(img, cv.COLOR_BGRA2BGR)

        # Lazy-init: detect actual capture resolution on first frame
        if self._scale_x is None:
            self._actual_width = img.shape[1]
            self._actual_height = img.shape[0]
            self._scale_x = self._actual_width / self.REFERENCE_WIDTH
            self._scale_y = self._actual_height / self.REFERENCE_HEIGHT

            log(f"[INFO] 📐 Capture resolution: {self._actual_width}x{self._actual_height}")
            log(f"[INFO] 📐 Scale factors: x={self._scale_x:.3f}, y={self._scale_y:.3f}")

            if self._actual_width != self.screen_config.monitor_width:
                log(f"[INFO] ⚠️ DPI mismatch detected! pywinctl={self.screen_config.monitor_width}x{self.screen_config.monitor_height}, "
                    f"actual capture={self._actual_width}x{self._actual_height}")

        return img

    def _scale_roi(self, roi):
        """Scale a reference ROI (x, y, w, h) to actual capture coordinates."""
        x, y, w, h = roi
        return (
            int(x * self._scale_x),
            int(y * self._scale_y),
            int(w * self._scale_x),
            int(h * self._scale_y),
        )

    def _perform_match(self, search_area, template_data):
        template_img, mask = template_data

        search_gray = cv.cvtColor(search_area, cv.COLOR_BGR2GRAY)
        template_gray = cv.cvtColor(template_img, cv.COLOR_BGR2GRAY)

        if search_gray.shape[0] < template_gray.shape[0] or search_gray.shape[1] < template_gray.shape[1]:
            return None, None

        result = cv.matchTemplate(search_gray, template_gray, cv.TM_CCOEFF_NORMED, mask=mask)
        _, confidence, _, location = cv.minMaxLoc(result)
        return confidence, location

    def _calculate_center(self, location, template_shape, ref_roi):
        """Calculate the click position in actual screen coordinates.
        
        location: match position within the (resized-to-reference) search area
        template_shape: (h, w) of the template
        ref_roi: the original reference ROI (x, y, w, h) in 1920x1080 space
        """
        h_t, w_t = template_shape
        ref_x, ref_y = ref_roi[0], ref_roi[1]

        # Position in 1080p reference space (within the game window)
        pos_ref_x = ref_x + location[0] + w_t // 2
        pos_ref_y = ref_y + location[1] + h_t // 2

        # Scale to actual capture pixels, then add window offset
        # Use actual capture dimensions for scaling (handles DPI mismatch)
        actual_scale_x = self._actual_width / self.REFERENCE_WIDTH
        actual_scale_y = self._actual_height / self.REFERENCE_HEIGHT
        
        # But for click coordinates we need screen coordinates (logical pixels)
        # The controller uses screen coordinates, so we scale by screen_config dimensions
        screen_scale_x = self.screen_config.monitor_width / self.REFERENCE_WIDTH
        screen_scale_y = self.screen_config.monitor_height / self.REFERENCE_HEIGHT

        return (
            int(pos_ref_x * screen_scale_x) + self.screen_config.monitor_x,
            int(pos_ref_y * screen_scale_y) + self.screen_config.monitor_y
        )

    def find(self, screen, template_name, radius=0, debug=False):
        if template_name not in self.templates:
            log(f"[INFO] ❌ Template '{template_name}' was not loaded.")
            return None

        if self._scale_x is None:
            return None

        template_data = self.templates[template_name]
        template_img, _ = template_data

        # Get the ROI config (in reference 1920x1080 coordinates)
        roi_config = self.detection_config.rois.get(template_name)
        if isinstance(roi_config, str):
            roi_config = self.detection_config.rois.get(roi_config)

        if not roi_config:
            # No ROI defined: search full screen (expensive)
            # Resize full screen to reference size for matching
            ref_frame = cv.resize(screen, (self.REFERENCE_WIDTH, self.REFERENCE_HEIGHT),
                                  interpolation=cv.INTER_AREA)
            confidence, location = self._perform_match(ref_frame, template_data)
            if confidence is not None and confidence >= self.detection_config.precision:
                if debug:
                    log(f"[DEBUG] [{template_name}] Full-screen match confidence: {confidence:.2%}")
                return self._calculate_center(location, template_img.shape[:2], (0, 0, self.REFERENCE_WIDTH, self.REFERENCE_HEIGHT))
            return None

        ref_roi = roi_config  # (x, y, w, h) in 1920x1080 space

        # Try matching at the primary ROI position and concentric offsets
        result = self._try_match_at_roi(screen, template_name, template_data, template_img, ref_roi, debug)
        if result is not None:
            return result

        # Concentric search around the ROI (shifted positions)
        if radius > 0:
            ref_x, ref_y, ref_w, ref_h = ref_roi
            step = max(1, int(5 * self._scale_x))  # Step size in native pixels, scaled from ~5px at 1080p
            
            for r in range(1, radius + 1):
                offsets = []
                offset_ref = r * 5  # 5 reference pixels per radius step
                # 4 cardinal directions
                offsets.append((ref_x + offset_ref, ref_y, ref_w, ref_h))
                offsets.append((ref_x - offset_ref, ref_y, ref_w, ref_h))
                offsets.append((ref_x, ref_y + offset_ref, ref_w, ref_h))
                offsets.append((ref_x, ref_y - offset_ref, ref_w, ref_h))
                # 4 diagonal directions
                offsets.append((ref_x + offset_ref, ref_y + offset_ref, ref_w, ref_h))
                offsets.append((ref_x - offset_ref, ref_y + offset_ref, ref_w, ref_h))
                offsets.append((ref_x + offset_ref, ref_y - offset_ref, ref_w, ref_h))
                offsets.append((ref_x - offset_ref, ref_y - offset_ref, ref_w, ref_h))

                for shifted_roi in offsets:
                    result = self._try_match_at_roi(screen, template_name, template_data, template_img, shifted_roi, debug)
                    if result is not None:
                        return result

        return None

    def _try_match_at_roi(self, screen, template_name, template_data, template_img, ref_roi, debug):
        """Try to match a template within a specific ROI.
        
        1. Scale ROI to native capture coordinates
        2. Crop from native screenshot
        3. Resize crop to reference ROI size (INTER_AREA)
        4. Match against original template
        """
        ref_x, ref_y, ref_w, ref_h = ref_roi

        # Scale ROI to actual capture coordinates
        nat_x = int(ref_x * self._scale_x)
        nat_y = int(ref_y * self._scale_y)
        nat_w = int(ref_w * self._scale_x)
        nat_h = int(ref_h * self._scale_y)

        # Clamp to screen bounds
        screen_h, screen_w = screen.shape[:2]
        nat_x = max(0, min(nat_x, screen_w - 1))
        nat_y = max(0, min(nat_y, screen_h - 1))
        nat_w = min(nat_w, screen_w - nat_x)
        nat_h = min(nat_h, screen_h - nat_y)

        if nat_w <= 0 or nat_h <= 0:
            return None

        # Crop at native resolution
        crop = screen[nat_y:nat_y + nat_h, nat_x:nat_x + nat_w]

        # Resize crop to reference ROI size using INTER_AREA (optimal for downscaling)
        if crop.shape[1] != ref_w or crop.shape[0] != ref_h:
            interpolation = cv.INTER_AREA if (crop.shape[1] > ref_w) else cv.INTER_LINEAR
            crop = cv.resize(crop, (ref_w, ref_h), interpolation=interpolation)

        # Match template against the reference-sized crop
        confidence, location = self._perform_match(crop, template_data)

        if confidence is None:
            return None

        precision = self.detection_config.precision
        is_match = confidence >= precision

        if debug and confidence >= 0.3:
            status = 'MATCH' if is_match else 'NO MATCH'
            log(f"[DEBUG] [{template_name}] Confidence: {confidence:.2%} (required: {precision:.0%}) -> {status}")

        if is_match:
            return self._calculate_center(location, template_img.shape[:2], ref_roi)

        return None
