"""Manages screenshot capture and storage."""
import time
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class ScreenshotRecord:
    """Record of a captured screenshot with metadata."""

    path: str
    description: str
    action_type: str
    timestamp: float
    element_target: Optional[str] = None
    step_number: int = 0


class ScreenshotManager:
    """Manages when and how to capture screenshots."""

    def __init__(self, output_dir: Path):
        """
        Initialize screenshot manager.

        Args:
            output_dir: Directory to store screenshots
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.screenshots: List[ScreenshotRecord] = []
        self.step_counter = 0

        logger.info(f"ScreenshotManager initialized: {self.output_dir}")

    def add_screenshot(
        self,
        screenshot_path: str,
        description: str,
        action_type: str,
        element_target: Optional[str] = None
    ) -> ScreenshotRecord:
        """
        Add a screenshot record.

        Args:
            screenshot_path: Path to the screenshot file
            description: Human-readable description
            action_type: Type of action performed
            element_target: Target element (if applicable)

        Returns:
            ScreenshotRecord
        """
        self.step_counter += 1

        record = ScreenshotRecord(
            path=screenshot_path,
            description=description,
            action_type=action_type,
            element_target=element_target,
            timestamp=time.time(),
            step_number=self.step_counter
        )

        self.screenshots.append(record)
        logger.info(f"Screenshot added: Step {self.step_counter} - {description}")

        return record

    def get_all_screenshots(self) -> List[ScreenshotRecord]:
        """Get all screenshot records."""
        return self.screenshots

    def get_screenshot_by_step(self, step_number: int) -> Optional[ScreenshotRecord]:
        """Get screenshot by step number."""
        for screenshot in self.screenshots:
            if screenshot.step_number == step_number:
                return screenshot
        return None

    def clear(self):
        """Clear all screenshot records."""
        self.screenshots = []
        self.step_counter = 0
        logger.info("Screenshot records cleared")
