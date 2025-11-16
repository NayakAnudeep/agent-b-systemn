"""Main DocumentationAgent orchestrator."""
import asyncio
import os
import time
import yaml
from pathlib import Path
from typing import Optional, Dict, List
from loguru import logger
from dotenv import load_dotenv

from src.browser.controller import BrowserController
from src.agent.vision_agent import VisionWebAgent
from src.browser.vision_login_agent import VisionLoginAgent
from src.browser.auth_handler import AuthHandler
from src.detection.state_detector import StateDetector
from src.screenshot.manager import ScreenshotManager
from src.screenshot.guide_generator import GuideGenerator


class DocumentationAgent:
    """
    Main orchestrator for Agent B - the web task documentation system.

    This agent receives questions like "How do I create a project in Linear?",
    navigates the web app, captures screenshots, and returns a visual guide.
    """

    def __init__(
        self,
        llm_provider: str = "claude",
        model: Optional[str] = None,
        config_path: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize the documentation agent.

        Args:
            llm_provider: "claude" or "openai"
            model: Specific model name (optional)
            config_path: Path to config YAML file
            api_key: API key for LLM provider (or set via env)
        """
        # Load environment variables
        load_dotenv()

        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "settings.yaml"

        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        # Get API key
        if api_key is None:
            if llm_provider == "claude":
                api_key = os.getenv("ANTHROPIC_API_KEY")
            else:
                api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(f"API key not found for {llm_provider}")

        # Initialize components
        self.llm_provider = llm_provider
        self.model = model or self.config["llm"]["providers"][llm_provider]["model"]

        self.browser: Optional[BrowserController] = None
        self.vision_agent: Optional[VisionWebAgent] = None
        self.login_agent: Optional[VisionLoginAgent] = None
        self.state_detector: Optional[StateDetector] = None
        self.screenshot_manager: Optional[ScreenshotManager] = None
        self.guide_generator = GuideGenerator()

        # Store API key for later initialization
        self._api_key = api_key

        logger.info(f"DocumentationAgent initialized with {llm_provider}/{self.model}")

    async def document_task(
        self,
        question: str,
        app_url: str,
        credentials: Optional[Dict[str, str]] = None,
        output_dir: Optional[str] = None,
        max_steps: int = 50
    ) -> Dict:
        """
        Main method to document a web task.

        Args:
            question: The task question (e.g., "How do I create a project in Linear?")
            app_url: Starting URL of the web application
            credentials: Optional dict with login credentials
            output_dir: Directory to save screenshots and guide
            max_steps: Maximum number of steps to prevent infinite loops

        Returns:
            Dictionary with steps, screenshots, and metadata
        """
        logger.info(f"Starting documentation task: '{question}'")
        logger.info(f"Target URL: {app_url}")

        # Setup output directory
        if output_dir is None:
            timestamp = int(time.time())
            output_dir = f"./output/{timestamp}"

        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {output_path}")

        # Initialize components
        self.browser = BrowserController(self.config["browser"])
        self.vision_agent = VisionWebAgent(
            provider=self.llm_provider,
            model=self.model,
            api_key=self._api_key,
            config=self.config["llm"]["providers"][self.llm_provider]
        )
        self.login_agent = VisionLoginAgent(
            provider=self.llm_provider,
            model=self.model,
            api_key=self._api_key
        )
        self.state_detector = StateDetector(self.config["detection"])
        self.screenshot_manager = ScreenshotManager(output_path)

        start_time = time.time()

        try:
            # Start browser
            await self.browser.start()

            # Navigate to starting URL
            await self.browser.navigate(app_url)

            # Use SPA detector for better stability
            if self.browser.spa_detector:
                await self.browser.spa_detector.wait_for_spa_ready()
            else:
                await self.browser.wait_for_stability()

            # Handle login if credentials provided
            if credentials:
                logger.info("Starting vision-based login...")

                login_success = await self._handle_login(credentials, max_login_steps=10)

                if not login_success:
                    logger.warning("⚠️ Vision-based login did not complete successfully")
                    logger.info("Task will continue - main agent may handle remaining steps")
                else:
                    logger.info("✅ Vision-based login completed successfully")

                    # Wait for app to be ready after login
                    if self.browser.spa_detector:
                        await self.browser.spa_detector.wait_for_spa_ready()
                    await self.browser.wait_for_stability()

            # Main agent loop
            task_complete = False
            step_count = 0

            while not task_complete and step_count < max_steps:
                step_count += 1
                logger.info(f"\n{'='*60}")
                logger.info(f"STEP {step_count}")
                logger.info(f"{'='*60}")

                # Capture current state
                current_state = await self.browser.get_current_state(
                    screenshot_dir=output_path
                )

                logger.info(f"Current URL: {current_state.url}")
                logger.info(f"Found {len(current_state.elements)} interactive elements")

                # Get decision from vision agent
                agent_response = self.vision_agent.decide_next_action(
                    goal=question,
                    current_state=current_state,
                    screenshot_path=current_state.screenshot_path
                )

                action = agent_response.action
                logger.info(f"Action: {action.action_type}")
                logger.info(f"Reasoning: {action.reasoning}")
                logger.info(f"Description: {action.step_description}")

                # Capture screenshot if recommended by agent
                if action.should_capture_screenshot:
                    self.screenshot_manager.add_screenshot(
                        screenshot_path=current_state.screenshot_path,
                        description=action.step_description,
                        action_type=action.action_type,
                        element_target=action.target
                    )

                # Check if task is complete
                if agent_response.is_task_complete:
                    logger.info("Task marked as complete by agent")
                    task_complete = True
                    break

                # Execute the action
                success = await self.browser.execute_action(action)

                if not success:
                    logger.warning(f"Action failed: {action.action_type}")
                    # Could implement retry logic here
                    await asyncio.sleep(1)
                    continue

                # Wait for UI to stabilize after action
                await self.browser.wait_for_stability()

                # Small pause between steps
                await asyncio.sleep(0.5)

            # Generate final guide
            logger.info("\n" + "="*60)
            logger.info("Generating documentation guide...")
            logger.info("="*60)

            screenshots = self.screenshot_manager.get_all_screenshots()

            # Generate multiple formats
            markdown_path = output_path / "guide.md"
            json_path = output_path / "guide.json"
            html_path = output_path / "guide.html"

            self.guide_generator.generate_markdown(screenshots, question, markdown_path)
            guide_data = self.guide_generator.generate_json(screenshots, question, json_path)
            self.guide_generator.generate_html(screenshots, question, html_path)

            # Build result
            duration = time.time() - start_time

            result = {
                "success": task_complete,
                "question": question,
                "total_steps": len(screenshots),
                "total_duration": f"{duration:.1f}s",
                "steps": [
                    {
                        "step_number": s.step_number,
                        "screenshot": s.path,
                        "description": s.description,
                        "action": s.action_type,
                        "timestamp": s.timestamp
                    }
                    for s in screenshots
                ],
                "output_directory": str(output_path),
                "guides": {
                    "markdown": str(markdown_path),
                    "json": str(json_path),
                    "html": str(html_path)
                }
            }

            logger.info(f"\n✅ Task completed in {duration:.1f}s")
            logger.info(f"📁 Output directory: {output_path}")
            logger.info(f"📸 Total screenshots: {len(screenshots)}")

            return result

        except Exception as e:
            logger.error(f"Task failed with error: {e}")
            import traceback
            traceback.print_exc()

            return {
                "success": False,
                "error": str(e),
                "question": question
            }

        finally:
            # Cleanup
            if self.browser:
                await self.browser.stop()

    async def _handle_login(self, credentials: Dict[str, str], max_login_steps: int = 10) -> bool:
        """
        Handle login flow using hybrid DOM + Vision authentication.

        Args:
            credentials: Dictionary with 'email' and 'password' keys
            max_login_steps: Maximum number of steps for login

        Returns:
            bool: True if login successful
        """
        logger.info("🔐 Starting hybrid DOM + Vision login...")

        # Get output directory from screenshot manager
        screenshot_dir = self.screenshot_manager.output_dir if self.screenshot_manager else None

        # Create hybrid auth handler with vision fallback support
        auth_handler = AuthHandler(
            vision_agent=self.login_agent,
            page=self.browser.page,
            som_marker=self.browser.som_marker,
            action_executor=self.browser.action_executor
        )

        # Use the new hybrid authentication
        success = await auth_handler.authenticate(
            credentials=credentials,
            max_steps=max_login_steps,
            screenshot_dir=screenshot_dir
        )

        return success

    async def _trigger_login_page(self) -> bool:
        """
        Try to find and click login/signin button to trigger login page.

        Returns:
            bool: True if login page triggered
        """
        logger.info("Looking for login/signin button...")

        try:
            # Try to find "Log in" link/button (prioritize login over signup)
            login_patterns = [
                ("Log in", True),      # Exact match for "Log in"
                ("Sign in", True),     # Exact match for "Sign in"
                ("Login", True),       # Exact match for "Login"
            ]

            for pattern, exact in login_patterns:
                try:
                    button = self.browser.page.get_by_role("link", name=pattern, exact=exact).first
                    if await button.is_visible(timeout=500):
                        logger.info(f"Found login link: '{pattern}'")
                        await button.click()
                        await asyncio.sleep(2)
                        return True
                except Exception:
                    pass

                try:
                    button = self.browser.page.get_by_role("button", name=pattern, exact=exact).first
                    if await button.is_visible(timeout=500):
                        logger.info(f"Found login button: '{pattern}'")
                        await button.click()
                        await asyncio.sleep(2)
                        return True
                except Exception:
                    pass

            # Try by text content
            try:
                button = self.browser.page.get_by_text("Log in", exact=True).first
                if await button.is_visible(timeout=500):
                    logger.info("Found 'Log in' by text")
                    await button.click()
                    await asyncio.sleep(2)
                    return True
            except Exception:
                pass

            # Try common selectors
            login_selectors = [
                'a[href*="login"]',
                'a[href*="signin"]',
                'a[href="/login"]',
                '[data-testid*="login"]',
                '[data-testid*="signin"]'
            ]

            for selector in login_selectors:
                try:
                    element = self.browser.page.locator(selector).first
                    if await element.is_visible(timeout=500):
                        logger.info(f"Found login element: {selector}")
                        await element.click()
                        await asyncio.sleep(2)
                        return True
                except Exception:
                    continue

            return False

        except Exception as e:
            logger.error(f"Error triggering login page: {e}")
            return False


async def main():
    """Example usage of DocumentationAgent."""
    # Example: Document a simple task
    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    result = await agent.document_task(
        question="How do I search for Python on Google?",
        app_url="https://www.google.com"
    )

    print("\n" + "="*60)
    print("RESULT")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Total steps: {result.get('total_steps', 0)}")
    print(f"Duration: {result.get('total_duration', 'N/A')}")

    if result.get('guides'):
        print(f"\nGenerated guides:")
        for format_type, path in result['guides'].items():
            print(f"  - {format_type}: {path}")


if __name__ == "__main__":
    asyncio.run(main())
