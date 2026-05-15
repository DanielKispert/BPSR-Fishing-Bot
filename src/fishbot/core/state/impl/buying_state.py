from ..bot_state import BotState
from ..state_type import StateType
from src.fishbot.utils.logger import log


class BuyingState(BotState):
    """Handles auto-purchasing rods or bait from the NPC shop.

    Triggered when:
    - CheckingRodState detects no rod AND inventory has none to equip
    - Bait slot is empty (checked before casting)

    Requires shop template images in assets/templates/:
    - shop_icon.png: The shop vendor tab/button after pressing B
    - shop_rod_tab.png: Rod category tab in the shop
    - shop_bait_tab.png: Bait category tab (special bait)
    - shop_bait_cheap_tab.png: Cheap bait category tab
    - shop_quantity.png: The quantity input field
    - shop_buy_btn.png: The Buy button
    - shop_confirm.png: Confirmation dialog Yes button
    - shop_close.png: The X/close button

    Screenshot instructions:
    1. Open the shop (press B near fishing vendor)
    2. Screenshot each UI element at 1920x1080 resolution
    3. Crop tightly around the element (leave 2-5px margin)
    4. Save as PNG in src/fishbot/assets/templates/
    """

    MAX_RETRIES = 3
    MAX_BUY_ATTEMPTS = 3

    def __init__(self, bot):
        super().__init__(bot)
        self._buy_item = None  # "rod" or "bait"
        self._consecutive_failures = 0

    def on_enter(self):
        # _buy_item is set externally before transition
        pass

    def set_buy_target(self, item_type):
        """Set what to buy: 'rod' or 'bait'. Call before transitioning to this state."""
        self._buy_item = item_type

    def handle(self, screen):
        if self._buy_item is None:
            log("[BUYING] ⚠️ No buy target set, returning to CHECKING_ROD")
            return StateType.CHECKING_ROD

        # Check if shop templates exist (graceful degradation)
        if not self._templates_available():
            log(f"[BUYING] ⚠️ Shop templates not found! Cannot auto-buy {self._buy_item}.")
            log("[BUYING] ℹ️ Add shop template images to assets/templates/ (see BuyingState docstring)")
            self._buy_item = None
            return StateType.CHECKING_ROD

        self.bot.log(f"[BUYING] 🛒 Auto-buying: {self._buy_item}")

        success = self._execute_purchase()

        self._buy_item = None

        if success:
            self._consecutive_failures = 0
            self.bot.log("[BUYING] ✅ Purchase complete, returning to rod check")
        else:
            self._consecutive_failures += 1
            self.bot.log("[BUYING] ❌ Purchase failed, returning to rod check anyway")
            if self._consecutive_failures >= self.MAX_BUY_ATTEMPTS:
                self.bot.log("[BUYING] ❌ Max purchase attempts reached! Stopping bot.")
                self.bot.stop()
                return StateType.BUYING

        return StateType.CHECKING_ROD

    def _templates_available(self):
        """Check if the essential shop templates are loaded."""
        essential = ["shop_icon", "shop_buy_btn", "shop_close"]
        for tmpl in essential:
            if tmpl not in self.detector.templates:
                return False
        return True

    def _execute_purchase(self):
        """Execute the full shop purchase flow. Returns True on success."""

        # Step 1: Open shop (press B)
        self.bot.log("[BUYING] 📂 Opening shop (pressing 'B')...")
        self.controller.press_key('b')
        if self.bot.sleep_or_stop(1.5):
            return False

        # Step 2: Find and click shop icon/tab
        shop_pos = self._find_with_retry("shop_icon", retries=3)
        if not shop_pos:
            self.bot.log("[BUYING] ❌ Could not find shop UI")
            self._close_shop()
            return False

        if self.controller.click_at_reliable(shop_pos[0], shop_pos[1], self.bot):
            return False
        if self.bot.sleep_or_stop(1.0):
            return False

        # Step 3: Click item category
        if self._buy_item == "rod":
            tab_template = "shop_rod_tab"
        elif self.config.auto_buy_bait_type == "cheap":
            tab_template = "shop_bait_cheap_tab"
        else:
            tab_template = "shop_bait_tab"

        tab_pos = self._find_with_retry(tab_template, retries=3)
        if not tab_pos:
            self.bot.log(f"[BUYING] ❌ Could not find {tab_template}")
            self._close_shop()
            return False

        if self.controller.click_at_reliable(tab_pos[0], tab_pos[1], self.bot):
            return False
        if self.bot.sleep_or_stop(0.8):
            return False

        # Step 4: Set quantity
        qty_pos = self._find_with_retry("shop_quantity", retries=2)
        if qty_pos:
            if self.controller.click_at_reliable(qty_pos[0], qty_pos[1], self.bot):
                return False
            if self.bot.sleep_or_stop(0.5):
                return False

            # Clear field by sending backspaces, then type quantity
            quantity = str(self.config.auto_buy_quantity)
            self.controller.press_key('backspace')
            if self.bot.sleep_or_stop(0.1):
                return False
            self.controller.press_key('backspace')
            if self.bot.sleep_or_stop(0.1):
                return False
            self.controller.press_key('backspace')
            if self.bot.sleep_or_stop(0.1):
                return False

            # Type each digit
            for digit in quantity:
                self.controller.press_key(digit)
                if self.bot.sleep_or_stop(0.1):
                    return False

            if self.bot.sleep_or_stop(0.3):
                return False

            # Confirm quantity (click OK button if present)
            ok_pos = self._find_with_retry("shop_ok_btn", retries=2)
            if ok_pos:
                if self.controller.click_at_reliable(ok_pos[0], ok_pos[1], self.bot):
                    return False
                if self.bot.sleep_or_stop(0.5):
                    return False
        else:
            self.bot.log("[BUYING] ⚠️ Quantity field not found, buying with default quantity")

        # Step 5: Click Buy button
        buy_pos = self._find_with_retry("shop_buy_btn", retries=3)
        if not buy_pos:
            self.bot.log("[BUYING] ❌ Could not find Buy button")
            self._close_shop()
            return False

        if self.controller.click_at_reliable(buy_pos[0], buy_pos[1], self.bot):
            return False
        if self.bot.sleep_or_stop(1.0):
            return False

        # Step 6: Handle confirmation dialog (bait purchases have a confirm dialog)
        if self._buy_item == "bait":
            screen = self.detector.capture_screen()
            confirm_pos = self.detector.find(screen, "shop_confirm", 5)
            if confirm_pos:
                if self.controller.click_at_reliable(confirm_pos[0], confirm_pos[1], self.bot):
                    return False
                if self.bot.sleep_or_stop(0.8):
                    return False

        # Step 7: Close shop
        self._close_shop()

        return True

    def _close_shop(self):
        """Close the shop UI."""
        if self.bot.sleep_or_stop(0.5):
            return
        screen = self.detector.capture_screen()
        close_pos = self.detector.find(screen, "shop_close", 5)
        if close_pos:
            self.controller.click_at_reliable(close_pos[0], close_pos[1], self.bot)
            self.bot.sleep_or_stop(0.5)
        else:
            # Fallback: press ESC to close any open UI
            self.controller.press_key('esc')
            self.bot.sleep_or_stop(0.5)

    def _find_with_retry(self, template_name, retries=3):
        """Try to find a template with retries and fresh screen captures."""
        for attempt in range(retries):
            if self.bot.is_stopped():
                return None
            screen = self.detector.capture_screen()
            pos = self.detector.find(screen, template_name, 5)
            if pos:
                return pos
            if attempt < retries - 1:
                self.bot.sleep_or_stop(0.5)
        return None
