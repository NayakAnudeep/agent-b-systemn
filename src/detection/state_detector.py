"""UI state change detection for determining when to capture screenshots."""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional
from skimage.metrics import structural_similarity as ssim
from loguru import logger


class StateDetector:
    """Detects significant UI state changes."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize state detector.

        Args:
            config: Configuration with thresholds
        """
        self.config = config or {
            "visual_similarity_threshold": 0.95,
            "dom_stability_checks": 3
        }

        self.last_screenshot_path: Optional[str] = None
        self.last_dom_hash: Optional[str] = None

    def has_significant_visual_change(
        self,
        current_screenshot: str,
        previous_screenshot: Optional[str] = None
    ) -> bool:
        """
        Detect if there's a significant visual change between screenshots.

        Args:
            current_screenshot: Path to current screenshot
            previous_screenshot: Path to previous screenshot (or use last)

        Returns:
            bool: True if significant change detected
        """
        if previous_screenshot is None:
            previous_screenshot = self.last_screenshot_path

        if previous_screenshot is None:
            # No previous screenshot, consider it a change
            self.last_screenshot_path = current_screenshot
            return True

        try:
            # Load images
            img1 = cv2.imread(previous_screenshot)
            img2 = cv2.imread(current_screenshot)

            if img1 is None or img2 is None:
                logger.warning("Failed to load screenshots for comparison")
                return True

            # Resize to same dimensions if needed
            if img1.shape != img2.shape:
                img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            # Calculate structural similarity
            similarity_score, _ = ssim(gray1, gray2, full=True)

            logger.debug(f"Visual similarity: {similarity_score:.3f}")

            # Update last screenshot
            self.last_screenshot_path = current_screenshot

            # Return True if similarity is below threshold (i.e., significant change)
            threshold = self.config["visual_similarity_threshold"]
            return similarity_score < threshold

        except Exception as e:
            logger.error(f"Visual comparison failed: {e}")
            return True  # Assume change on error

    def has_dom_change(self, current_hash: str) -> bool:
        """
        Check if DOM has changed.

        Args:
            current_hash: Current DOM hash

        Returns:
            bool: True if DOM changed
        """
        if self.last_dom_hash is None:
            self.last_dom_hash = current_hash
            return True

        changed = current_hash != self.last_dom_hash
        self.last_dom_hash = current_hash

        return changed

    def should_capture_screenshot(
        self,
        action_type: str,
        current_screenshot: Optional[str] = None,
        current_dom_hash: Optional[str] = None
    ) -> bool:
        """
        Determine if a screenshot should be captured.

        Args:
            action_type: Type of action being performed
            current_screenshot: Path to current screenshot for visual comparison
            current_dom_hash: Current DOM hash for change detection

        Returns:
            bool: True if screenshot should be captured
        """
        # Always capture for milestone actions
        milestone_actions = {"click", "navigate", "done"}
        if action_type in milestone_actions:
            logger.debug(f"Capture recommended: milestone action '{action_type}'")
            return True

        # Check for visual changes if screenshot provided
        if current_screenshot:
            visual_change = self.has_significant_visual_change(current_screenshot)
            if visual_change:
                logger.debug("Capture recommended: significant visual change")
                return True

        # Check for DOM changes if hash provided
        if current_dom_hash:
            dom_change = self.has_dom_change(current_dom_hash)
            if dom_change:
                logger.debug("Capture recommended: DOM change detected")
                return True

        logger.debug("No capture needed: no significant changes")
        return False

    def reset(self):
        """Reset detector state."""
        self.last_screenshot_path = None
        self.last_dom_hash = None
        logger.debug("StateDetector reset")
