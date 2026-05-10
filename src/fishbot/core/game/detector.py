import cv2 as cv
import numpy as np
import time
from pathlib import Path

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

    # Base scales - the dynamic reciprocal scale is added after first capture
    MATCH_SCALES_BASE = [0.8, 1.0, 1.2, 1.6]

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

        # Cache: once a template matches at a certain scale, prioritize it
        self._scale_cache = {}
        self._match_scales = list(self.MATCH_SCALES_BASE)

        # Screenshot capture for debugging - use CWD-relative path for portability
        self._last_screenshot_time = 0
        self._screenshot_dir = Path.cwd() / "logs" / "screenshots"
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
        self._max_screenshots = 60
        log(f"[INFO] 📸 Screenshots will be saved to: {self._screenshot_dir}")

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

            # Add dynamic scale: reciprocal of capture scale (for games where UI doesn't scale)
            reciprocal = round(1.0 / self._scale_x, 2)
            if reciprocal not in self._match_scales:
                self._match_scales.insert(0, reciprocal)  # Highest priority
            log(f"[INFO] 📐 Match scales: {self._match_scales}")

        # Save debug screenshot once per second (scaled to reference resolution)
        now = time.time()
        if now - self._last_screenshot_time >= 1.0:
            self._last_screenshot_time = now
            self._save_debug_screenshot(img)

        return img

    def _save_debug_screenshot(self, img):
        """Save a screenshot scaled to 1920x1080 for offline debugging."""
        try:
            ref_img = cv.resize(img, (self.REFERENCE_WIDTH, self.REFERENCE_HEIGHT), interpolation=cv.INTER_AREA)
            timestamp = time.strftime("%H%M%S")
            filepath = self._screenshot_dir / f"frame_{timestamp}.png"
            success = cv.imwrite(str(filepath), ref_img)
            if success:
                log(f"[DEBUG] 📸 Saved: {filepath}")
            else:
                log(f"[ERROR] 📸 cv.imwrite returned False for: {filepath}")

            # Rolling buffer: delete oldest files if over limit
            files = sorted(self._screenshot_dir.glob("frame_*.png"))
            while len(files) > self._max_screenshots:
                files[0].unlink()
                files.pop(0)
        except Exception as e:
            log(f"[ERROR] 📸 Screenshot save failed: {type(e).__name__}: {e}")

    def save_timeout_frame(self, screen, state_name):
        """Save current frame when a state times out - critical for debugging."""
        try:
            ref_img = cv.resize(screen, (self.REFERENCE_WIDTH, self.REFERENCE_HEIGHT), interpolation=cv.INTER_AREA)
            timestamp = time.strftime("%H%M%S")
            filepath = self._screenshot_dir / f"timeout_{state_name}_{timestamp}.png"
            cv.imwrite(str(filepath), ref_img)
            log(f"[INFO] 📸 Timeout frame saved: {filepath.name}")
        except Exception as e:
            log(f"[ERROR] Timeout frame save failed: {e}")

    def _get_scales_for_template(self, template_name):
        """Get scales to try, prioritizing cached successful scale."""
        if template_name in self._scale_cache:
            cached = self._scale_cache[template_name]
            # Try cached scale first, then close neighbors, then all others
            priority = [cached]
            for s in self._match_scales:
                if abs(s - cached) <= 0.15 and s != cached:
                    priority.append(s)
            for s in self._match_scales:
                if s not in priority:
                    priority.append(s)
            return priority
        return self._match_scales

    def _perform_match_multiscale(self, search_area, template_data, template_name):
        """Try matching template at multiple scales. Returns (confidence, location, scale)."""
        template_img, mask = template_data
        search_gray = cv.cvtColor(search_area, cv.COLOR_BGR2GRAY)

        best_confidence = 0
        best_location = None
        best_scale = 1.0

        scales = self._get_scales_for_template(template_name)

        for scale in scales:
            new_w = max(1, int(template_img.shape[1] * scale))
            new_h = max(1, int(template_img.shape[0] * scale))

            if search_gray.shape[0] < new_h or search_gray.shape[1] < new_w:
                continue

            interp = cv.INTER_AREA if scale < 1 else cv.INTER_LINEAR
            scaled_template_gray = cv.resize(
                cv.cvtColor(template_img, cv.COLOR_BGR2GRAY),
                (new_w, new_h), interpolation=interp
            )

            scaled_mask = None
            if mask is not None:
                scaled_mask = cv.resize(mask, (new_w, new_h), interpolation=interp)

            try:
                result = cv.matchTemplate(search_gray, scaled_template_gray, cv.TM_CCOEFF_NORMED, mask=scaled_mask)
                _, confidence, _, location = cv.minMaxLoc(result)
            except cv.error:
                continue

            if confidence > best_confidence:
                best_confidence = confidence
                best_location = location
                best_scale = scale

                # Early exit if we found a good match
                if confidence >= 0.70:
                    break

        return best_confidence, best_location, best_scale

    def _calculate_center_native(self, location, scaled_template_shape, nat_offset_x, nat_offset_y):
        """Calculate click position from a match found in native pixel space."""
        scaled_h, scaled_w = scaled_template_shape

        # Center of match in native capture pixels
        center_nat_x = nat_offset_x + location[0] + scaled_w // 2
        center_nat_y = nat_offset_y + location[1] + scaled_h // 2

        # Convert from capture pixels to screen (logical) pixels
        screen_x = int(center_nat_x / self._actual_width * self.screen_config.monitor_width) + self.screen_config.monitor_x
        screen_y = int(center_nat_y / self._actual_height * self.screen_config.monitor_height) + self.screen_config.monitor_y

        return (screen_x, screen_y)

    def find(self, screen, template_name, radius=0, debug=False):
        if template_name not in self.templates:
            log(f"[INFO] ❌ Template '{template_name}' was not loaded.")
            return None

        if self._scale_x is None:
            return None

        template_data = self.templates[template_name]

        # Get the ROI config (in reference 1920x1080 coordinates)
        roi_config = self.detection_config.rois.get(template_name)
        if isinstance(roi_config, str):
            roi_config = self.detection_config.rois.get(roi_config)

        if not roi_config:
            # No ROI: search full screen with multi-scale
            return self._search_full_screen(screen, template_name, template_data, debug)

        ref_roi = roi_config

        # Try matching at the primary ROI position
        result = self._try_match_at_roi(screen, template_name, template_data, ref_roi, debug)
        if result is not None:
            return result

        # Concentric search around the ROI (shifted positions)
        if radius > 0:
            ref_x, ref_y, ref_w, ref_h = ref_roi
            for r in range(1, radius + 1):
                offset_ref = r * 5
                offsets = [
                    (ref_x + offset_ref, ref_y, ref_w, ref_h),
                    (ref_x - offset_ref, ref_y, ref_w, ref_h),
                    (ref_x, ref_y + offset_ref, ref_w, ref_h),
                    (ref_x, ref_y - offset_ref, ref_w, ref_h),
                    (ref_x + offset_ref, ref_y + offset_ref, ref_w, ref_h),
                    (ref_x - offset_ref, ref_y + offset_ref, ref_w, ref_h),
                    (ref_x + offset_ref, ref_y - offset_ref, ref_w, ref_h),
                    (ref_x - offset_ref, ref_y - offset_ref, ref_w, ref_h),
                ]
                for shifted_roi in offsets:
                    result = self._try_match_at_roi(screen, template_name, template_data, shifted_roi, debug=False)
                    if result is not None:
                        return result

        return None

    def _search_full_screen(self, screen, template_name, template_data, debug):
        """Search the full screen with multi-scale matching."""
        confidence, location, scale = self._perform_match_multiscale(screen, template_data, template_name)

        if confidence is None or location is None:
            return None

        precision = self.detection_config.precision
        is_match = confidence >= precision

        if debug:
            status = 'MATCH' if is_match else 'NO MATCH'
            log(f"[DEBUG] [{template_name}] Full-screen confidence: {confidence:.2%} @ scale {scale:.2f} (required: {precision:.0%}) -> {status}")

        if is_match:
            self._scale_cache[template_name] = scale
            template_img, _ = template_data
            scaled_w = int(template_img.shape[1] * scale)
            scaled_h = int(template_img.shape[0] * scale)
            return self._calculate_center_native(location, (scaled_h, scaled_w), 0, 0)

        return None

    def _try_match_at_roi(self, screen, template_name, template_data, ref_roi, debug):
        """Try to match a template within a specific ROI using multi-scale matching.

        1. Scale ROI to native capture coordinates
        2. Crop from native screenshot
        3. Multi-scale match template against native crop
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

        # Multi-scale matching against native crop
        confidence, location, scale = self._perform_match_multiscale(crop, template_data, template_name)

        if confidence is None or location is None:
            return None

        precision = self.detection_config.precision
        is_match = confidence >= precision

        if debug:
            status = 'MATCH' if is_match else 'NO MATCH'
            log(f"[DEBUG] [{template_name}] Confidence: {confidence:.2%} @ scale {scale:.2f} (required: {precision:.0%}) -> {status}")

        if is_match:
            self._scale_cache[template_name] = scale
            template_img, _ = template_data
            scaled_w = int(template_img.shape[1] * scale)
            scaled_h = int(template_img.shape[0] * scale)
            return self._calculate_center_native(location, (scaled_h, scaled_w), nat_x, nat_y)

        return None
