"""Browser automation controller using Playwright."""
import asyncio
import hashlib
from typing import Optional
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from loguru import logger

from src.browser.som_marker import SoMMarker
from src.browser.action_executor import ActionExecutor
from src.detection.spa_detector import SPADetector
from src.agent.schemas import PageState, ElementInfo


class BrowserController:
    """Manages browser automation with Playwright."""

    def __init__(self, config: Optional[dict] = None):
        """
        Initialize browser controller.

        Args:
            config: Browser configuration dictionary
        """
        self.config = config or {
            "headless": False,
            "viewport": {"width": 1280, "height": 720},
            "timeout": 30000
        }

        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.som_marker: Optional[SoMMarker] = None
        self.action_executor: Optional[ActionExecutor] = None
        self.spa_detector: Optional[SPADetector] = None

    async def start(self):
        """Start the browser and create a new page."""
        logger.info("Starting browser...")

        self.playwright = await async_playwright().start()

        # Launch with stealth args to avoid detection
        self.browser = await self.playwright.chromium.launch(
            headless=self.config["headless"],
            args=[
                '--disable-blink-features=AutomationControlled',  # Hide automation
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--allow-running-insecure-content',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )

        # Complete user agent string
        full_user_agent = self.config.get(
            "user_agent",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )

        self.context = await self.browser.new_context(
            viewport=self.config["viewport"],
            user_agent=full_user_agent,
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation', 'notifications'],
            ignore_https_errors=True
        )

        self.page = await self.context.new_page()
        self.page.set_default_timeout(self.config["timeout"])

        # Hide webdriver property to avoid detection
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });

            // Override chrome property
            window.navigator.chrome = {
                runtime: {}
            };

            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );

            // Override plugins to avoid headless detection
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });

            // Override languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
        """)

        # Initialize all components
        som_config = self.config.get("som_marker", {})
        self.som_marker = SoMMarker(som_config)
        self.action_executor = ActionExecutor(self.page, self.som_marker)
        self.spa_detector = SPADetector(self.page)

        logger.info("Browser started successfully with stealth mode")

    async def stop(self):
        """Stop the browser and clean up resources."""
        logger.info("Stopping browser...")

        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

        logger.info("Browser stopped")

    async def navigate(self, url: str):
        """Navigate to a URL."""
        if not self.page:
            raise RuntimeError("Browser not started. Call start() first.")

        logger.info(f"Navigating to {url}")
        try:
            # Use 'domcontentloaded' instead of 'networkidle' for heavy SPAs
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            logger.info("Page loaded (DOM ready)")
        except Exception as e:
            logger.warning(f"Navigation completed with warning: {e}")
            # Continue anyway - page might be loaded enough

        await asyncio.sleep(2)  # Additional stability wait

    async def get_current_state(self, screenshot_dir: Optional[Path] = None) -> PageState:
        """
        Capture the current page state including screenshot and element info.

        Args:
            screenshot_dir: Directory to save screenshot (optional)

        Returns:
            PageState object
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        # Get basic page info
        url = self.page.url
        title = await self.page.title()

        # Mark page and get element info
        elements_data = await self.som_marker.mark_page(self.page)

        # Convert to ElementInfo objects
        elements = [
            ElementInfo(
                marker_id=el["marker_id"],
                tag_name=el["tag_name"],
                text=el.get("text"),
                role=el.get("role"),
                aria_label=el.get("aria_label"),
                placeholder=el.get("placeholder"),
                href=el.get("href"),
                type=el.get("type")
            )
            for el in elements_data
        ]

        # Capture screenshot if directory provided
        screenshot_path = None
        if screenshot_dir:
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = screenshot_dir / f"state_{asyncio.get_event_loop().time()}.png"
            await self.page.screenshot(path=str(screenshot_path), full_page=False)
            logger.debug(f"Screenshot saved to {screenshot_path}")

        # Calculate DOM hash for change detection
        dom_content = await self.page.content()
        dom_hash = hashlib.md5(dom_content.encode()).hexdigest()

        return PageState(
            url=url,
            title=title,
            screenshot_path=str(screenshot_path) if screenshot_path else None,
            elements=elements,
            dom_hash=dom_hash,
            timestamp=asyncio.get_event_loop().time()
        )

    async def wait_for_stability(self, max_attempts: int = 10) -> bool:
        """
        Wait for the UI to stabilize (no DOM changes).

        Args:
            max_attempts: Maximum number of stability checks

        Returns:
            bool: True if stable, False if timed out
        """
        logger.debug("Waiting for UI to stabilize...")
        previous_hash = None
        stable_count = 0

        for i in range(max_attempts):
            await asyncio.sleep(0.3)

            # Get DOM snapshot
            try:
                dom = await self.page.content()
                current_hash = hashlib.md5(dom.encode()).hexdigest()

                if current_hash == previous_hash:
                    stable_count += 1
                    if stable_count >= 3:  # 3 consecutive stable checks
                        logger.debug("UI stabilized")
                        return True
                else:
                    stable_count = 0

                previous_hash = current_hash

            except Exception as e:
                logger.warning(f"Stability check failed: {e}")
                break

        # Also wait for network idle
        try:
            await self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:
            pass  # Timeout is ok

        logger.debug("UI stability check completed")
        return stable_count >= 2  # At least 2 stable checks

    async def capture_screenshot(
        self,
        path: str,
        full_page: bool = False,
        with_markers: bool = True
    ) -> str:
        """
        Capture a screenshot of the current page.

        Args:
            path: Path to save the screenshot
            full_page: Whether to capture the full scrollable page
            with_markers: Whether to include SoM markers

        Returns:
            Path to saved screenshot
        """
        if not self.page:
            raise RuntimeError("Browser not started")

        # Ensure markers are visible if requested
        if with_markers:
            await self.som_marker.mark_page(self.page)

        await self.page.screenshot(path=path, full_page=full_page)
        logger.info(f"Screenshot captured: {path}")

        return path

    async def execute_action(self, action):
        """
        Execute an agent action.

        Args:
            action: AgentAction object

        Returns:
            bool: Success status
        """
        if not self.action_executor:
            raise RuntimeError("Browser not started")

        return await self.action_executor.execute(action)

    async def remove_markers(self):
        """Remove SoM markers from the page."""
        if self.som_marker:
            await self.som_marker.remove_markers(self.page)

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.browser:
            asyncio.get_event_loop().run_until_complete(self.stop())
