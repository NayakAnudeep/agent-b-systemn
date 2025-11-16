"""Interactive chat interface for Agent B - General web automation."""
import asyncio
from dotenv import load_dotenv
import os
from loguru import logger
from src.browser.controller import BrowserController
from src.agent.vision_agent import VisionWebAgent
from src.browser.som_marker import SoMMarker
from src.browser.action_executor import ActionExecutor
from src.screenshot.manager import ScreenshotManager
from src.agent.schemas import PageState, ElementInfo
import time
import re

load_dotenv()


# Application registry - maps app names to URLs
APP_REGISTRY = {
    "notion": "https://www.notion.so",
    "linear": "https://linear.app",
    "github": "https://github.com",
    "jira": "https://www.atlassian.com/software/jira",
    "asana": "https://app.asana.com",
    "trello": "https://trello.com",
    "slack": "https://slack.com",
    "clickup": "https://app.clickup.com",
}


class WebAutomationAgent:
    """Interactive chat agent for automating tasks on any web application."""

    def __init__(self):
        """Initialize the chat agent."""
        self.browser = None
        self.current_url = None
        self.current_app = None
        self.is_logged_in = False
        self.credentials = None

    async def start(self):
        """Initialize and show welcome message."""
        print("\n" + "="*70)
        print("🤖 AGENT B - WEB AUTOMATION ASSISTANT")
        print("="*70)
        print("\nWelcome! I can help you automate tasks on any web application.")
        print("\n📋 Supported applications (with auto-login):")
        for app_name in sorted(APP_REGISTRY.keys()):
            print(f"  • {app_name}")
        print("\n💡 Just mention the app in your command, e.g.:")
        print("  • 'Create a todo list in notion'")
        print("  • 'Make a new project in linear'")
        print("  • 'Go to github.com and create an issue'")
        print("\nType 'help' for more info, 'exit' to quit\n")
        print("="*70)
        print("\n💡 I'll detect the app and auto-login when you give me a command.\n")
        return True

    def detect_app_from_task(self, task: str) -> str:
        """Detect which app is mentioned in the task."""
        task_lower = task.lower()

        # Check for explicit app mentions
        for app_name in APP_REGISTRY.keys():
            if app_name in task_lower:
                return app_name

        # Check for domain mentions (e.g., "notion.so", "linear.app")
        for app_name, url in APP_REGISTRY.items():
            domain = url.replace("https://", "").replace("http://", "")
            if domain in task_lower:
                return app_name

        return None

    async def setup_app(self, app_name: str):
        """Setup credentials and mark app for auto-navigation."""
        if self.current_app == app_name:
            return  # Already set up

        self.current_app = app_name

        # Get credentials from .env
        email_key = f"{app_name.upper()}_EMAIL"
        password_key = f"{app_name.upper()}_PASSWORD"

        email = os.getenv(email_key)
        password = os.getenv(password_key)

        if not email or not password:
            print(f"\n⚠️  Credentials for {app_name} not found in .env file!")
            print(f"Add these to your .env file for auto-login:")
            print(f"  {email_key}=your_email@example.com")
            print(f"  {password_key}=your_password")
            print(f"💡 Continuing anyway - you can login manually.\n")
            self.credentials = None
        else:
            print(f"\n✅ Detected app: {app_name} ({email})")
            self.credentials = {"email": email, "password": password}

    async def ensure_browser_started(self):
        """Ensure browser is started and navigate to app if configured."""
        if self.is_logged_in:
            return True

        if self.browser is None:
            print("\n⏳ Starting browser for the first time...")

            # Initialize browser
            self.browser = BrowserController(config={
                "headless": False,
                "viewport": {"width": 1280, "height": 720},
                "timeout": 30000
            })
            await self.browser.start()
            print("✅ Browser started")

            # Navigate to app if one was selected
            if self.current_app:
                app_url = APP_REGISTRY[self.current_app]
                print(f"⏳ Navigating to {self.current_app} ({app_url})...")
                await self.browser.navigate(app_url)
                await asyncio.sleep(2)
                self.current_url = app_url
                print(f"✅ Navigated to {self.current_app}")

                # Auto-login if credentials are available
                if self.credentials:
                    print(f"⏳ Logging in as {self.credentials['email']}...")

                    # Import required components
                    from src.browser.vision_login_agent import VisionLoginAgent
                    from src.browser.som_marker import SoMMarker
                    from src.browser.action_executor import ActionExecutor
                    from src.browser.auth_handler import AuthHandler

                    # Create output directory
                    os.makedirs("./output/chat_session", exist_ok=True)

                    # Initialize components for auth
                    vision_agent = VisionLoginAgent(provider="claude", model="claude-sonnet-4-20250514")
                    som_marker = SoMMarker()
                    action_executor = ActionExecutor(self.browser.page, som_marker)

                    auth_handler = AuthHandler(
                        vision_agent=vision_agent,
                        page=self.browser.page,
                        som_marker=som_marker,
                        action_executor=action_executor
                    )

                    success = await auth_handler.authenticate(
                        credentials=self.credentials,
                        screenshot_dir="./output/chat_session"
                    )

                    if success:
                        self.is_logged_in = True
                        print(f"✅ Successfully logged in to {self.current_app}!\n")
                        print("-" * 70)
                    else:
                        print(f"❌ Failed to login to {self.current_app}")
                        print("💡 You can login manually or try again\n")
                else:
                    print("💡 No credentials found - please login manually in the browser\n")

            return True

        return True

    async def navigate_to_url(self, url: str) -> bool:
        """Navigate to a specific URL."""
        # Ensure browser is started
        await self.ensure_browser_started()

        # Add https:// if not present
        if not url.startswith("http"):
            url = f"https://{url}"

        print(f"\n⏳ Navigating to {url}...")
        try:
            await self.browser.navigate(url)
            await asyncio.sleep(2)
            self.current_url = url
            print(f"✅ Navigated to {url}\n")
            return True
        except Exception as e:
            print(f"❌ Failed to navigate: {e}")
            return False

    async def execute_task(self, task: str) -> dict:
        """
        Execute a task on the current web page.

        Args:
            task: Natural language description of the task

        Returns:
            dict: Result with success status and message
        """
        # Detect app from task
        detected_app = self.detect_app_from_task(task)
        if detected_app and not self.current_app:
            await self.setup_app(detected_app)

        # Check if this is a navigation command
        nav_match = re.match(r'(?:go to|navigate to|open)\s+(.+)', task.lower())
        if nav_match:
            url = nav_match.group(1).strip()
            success = await self.navigate_to_url(url)
            return {
                "success": success,
                "message": f"Navigated to {url}" if success else "Navigation failed",
                "steps": 1
            }

        # Ensure browser is started (will auto-navigate and login if app is set)
        if not await self.ensure_browser_started():
            return {
                "success": False,
                "message": "Failed to start browser"
            }

        # Check if we're on a page
        if self.browser.page.url == "about:blank" or not self.current_url:
            print("\n⚠️  You need to navigate to a website or mention an app in your command.")
            print("Examples:")
            print("  • 'Create a todo list in notion'")
            print("  • 'go to notion.so'")
            print("  • 'Make a new project in linear'\n")
            return {
                "success": False,
                "message": "No website loaded. Please navigate to a website or mention an app."
            }

        print(f"\n🔄 Executing: {task}")
        print("-" * 70)

        try:
            # Initialize components
            from src.screenshot.guide_generator import GuideGenerator

            som_marker = SoMMarker()
            action_executor = ActionExecutor(self.browser.page, som_marker)
            vision_agent = VisionWebAgent(provider="claude", model="claude-sonnet-4-20250514")
            screenshot_manager = ScreenshotManager("./output/chat_session")
            guide_generator = GuideGenerator()

            # Execute task with vision agent
            max_steps = 20

            for step in range(1, max_steps + 1):
                print(f"\n📍 Step {step}/{max_steps}")

                # Get current state
                await som_marker.mark_page(self.browser.page)
                current_url = self.browser.page.url
                page_title = await self.browser.page.title()

                # Get element info
                elements_script = """
                () => {
                    const selectors = [
                        'button', 'a[href]', 'input:not([type="hidden"])', 'textarea',
                        'select', '[role="button"]', '[role="link"]', '[role="tab"]',
                        '[role="menuitem"]', '[onclick]', '[contenteditable="true"]',
                        'div[class*="button"]', 'div[class*="Button"]', 'span[class*="button"]',
                        '[class*="clickable"]', '[class*="interactive"]', '[data-clickable="true"]'
                    ];

                    const elements = Array.from(document.querySelectorAll(selectors.join(',')));
                    const visibleElements = elements.filter(el => {
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        return (
                            rect.width > 0 && rect.height > 0 &&
                            style.visibility !== 'hidden' &&
                            style.display !== 'none' &&
                            style.opacity !== '0'
                        );
                    });

                    const pointerElements = Array.from(document.querySelectorAll('div, span')).filter(el => {
                        const rect = el.getBoundingClientRect();
                        const style = window.getComputedStyle(el);
                        return (
                            style.cursor === 'pointer' &&
                            rect.width > 20 && rect.height > 15 &&
                            rect.width < 500 && rect.height < 200 &&
                            style.visibility !== 'hidden' &&
                            style.display !== 'none' &&
                            style.opacity !== '0'
                        );
                    });

                    const allInteractive = [...visibleElements, ...pointerElements];
                    const uniqueElements = Array.from(new Set(allInteractive));

                    return uniqueElements.slice(0, 50).map((el, idx) => ({
                        marker_id: idx,
                        tag_name: el.tagName.toLowerCase(),
                        text: el.textContent?.trim().substring(0, 100) || null,
                        role: el.getAttribute('role'),
                        aria_label: el.getAttribute('aria-label'),
                        placeholder: el.getAttribute('placeholder'),
                        href: el.getAttribute('href'),
                        type: el.getAttribute('type')
                    }));
                }
                """

                elements_data = await self.browser.page.evaluate(elements_script)

                # Convert to ElementInfo objects
                elements = [ElementInfo(**el) for el in elements_data]

                # Take screenshot
                screenshot_path = f"./output/chat_session/step_{step}.png"
                await self.browser.page.screenshot(path=screenshot_path)

                # Create PageState
                current_state = PageState(
                    url=current_url,
                    title=page_title,
                    screenshot_path=screenshot_path,
                    elements=elements,
                    timestamp=time.time()
                )

                # Decide next action
                agent_response = vision_agent.decide_next_action(
                    goal=task,
                    current_state=current_state,
                    screenshot_path=screenshot_path
                )

                action = agent_response.action

                print(f"  Action: {action.action_type}")
                print(f"  Reasoning: {action.reasoning}")
                print(f"  Description: {action.step_description}")

                # Add screenshot to manager (track for guide generation)
                screenshot_manager.add_screenshot(
                    screenshot_path=screenshot_path,
                    description=action.step_description,
                    action_type=action.action_type,
                    element_target=action.target
                )

                # Execute action
                if action.action_type == "done":
                    await som_marker.remove_markers(self.browser.page)
                    print("\n✅ Task completed successfully!")

                    # Generate HTML guide
                    await self._generate_guide(task, screenshot_manager, guide_generator)

                    return {
                        "success": True,
                        "message": action.step_description,
                        "steps": step
                    }

                success = await action_executor.execute(action)

                if success:
                    await self.browser.wait_for_stability()
                else:
                    print(f"  ⚠️  Action failed, continuing...")

                await som_marker.remove_markers(self.browser.page)
                await asyncio.sleep(0.5)

            print(f"\n⚠️  Reached max steps ({max_steps})")
            return {
                "success": False,
                "message": f"Task incomplete - reached max steps ({max_steps})",
                "steps": max_steps
            }

        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            print(f"\n❌ Error: {e}")
            return {
                "success": False,
                "message": str(e)
            }

    async def chat_loop(self):
        """Run the interactive chat loop."""
        while True:
            try:
                # Get user input
                user_input = input("\n💬 You: ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.lower() in ['exit', 'quit', 'q']:
                    print("\n👋 Goodbye!")
                    break

                if user_input.lower() == 'help':
                    self.print_help()
                    continue

                if user_input.lower() == 'status':
                    print(f"\n📊 Status:")
                    if self.browser:
                        print(f"  Browser: ✅ Running")
                        print(f"  Current URL: {self.browser.page.url}")
                    else:
                        print(f"  Browser: ❌ Not started")
                    continue

                # Execute the task
                result = await self.execute_task(user_input)

                # Show result
                if result["success"]:
                    print(f"\n🤖 Agent B: ✅ {result['message']}")
                    if 'steps' in result:
                        print(f"   Completed in {result['steps']} steps")
                else:
                    print(f"\n🤖 Agent B: ❌ {result['message']}")

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                logger.error(f"Chat loop error: {e}")
                print(f"\n❌ Error: {e}")

    async def _generate_guide(self, task: str, screenshot_manager, guide_generator):
        """Generate HTML guide from the task execution."""
        from pathlib import Path
        import re

        print("\n📝 Generating documentation guide...")

        # Get all screenshots
        screenshots = screenshot_manager.get_all_screenshots()

        if not screenshots:
            print("⚠️  No screenshots captured - skipping guide generation")
            return

        # Create safe filename from task
        safe_task_name = re.sub(r'[^a-zA-Z0-9\s]', '', task)
        safe_task_name = safe_task_name.replace(' ', '_').lower()[:50]

        # Create output directory
        guide_dir = Path(f"./output/guides/{safe_task_name}")
        guide_dir.mkdir(parents=True, exist_ok=True)

        # Generate HTML guide
        html_path = guide_dir / "guide.html"
        guide_generator.generate_html(
            screenshots=screenshots,
            task_goal=task,
            output_path=html_path
        )

        # Also generate JSON for programmatic access
        json_path = guide_dir / "guide.json"
        guide_generator.generate_json(
            screenshots=screenshots,
            task_goal=task,
            output_path=json_path
        )

        # Copy screenshots to guide directory
        import shutil
        for screenshot in screenshots:
            src = Path(screenshot.path)
            if src.exists():
                dst = guide_dir / src.name
                shutil.copy(src, dst)

        print(f"✅ Guide generated successfully!")
        print(f"📂 Location: {guide_dir}")
        print(f"🌐 HTML: {html_path}")
        print(f"📊 JSON: {json_path}")
        print(f"📸 Screenshots: {len(screenshots)} images")

    def print_help(self):
        """Print help information."""
        print("\n" + "="*70)
        print("📚 HELP - WEB AUTOMATION ASSISTANT")
        print("="*70)
        print("\nCommands:")
        print("  exit/quit/q  - Exit the chat")
        print("  help         - Show this help message")
        print("  status       - Show current status")
        print("\n🎯 Smart App Detection:")
        print("  Just mention the app name in your command!")
        print("\n  Examples:")
        print("    'Create a todo list in notion' → Detects notion, auto-logins")
        print("    'Make a new project in linear' → Detects linear, auto-logins")
        print("    'Create an issue in github'    → Detects github, auto-logins")
        print("\n📋 Supported apps:")
        print("  " + ", ".join(sorted(APP_REGISTRY.keys())))
        print("\n🌐 Manual Navigation:")
        print("  go to [URL]       - Navigate to any website")
        print("  navigate to [URL] - Same as above")
        print("  open [URL]        - Same as above")
        print("\n💡 Task Examples:")
        print("  • Create a database for tracking bugs in notion")
        print("  • Make a new project called 'Q1 Planning' in linear")
        print("  • Add a task to the board in trello")
        print("  • go to example.com")
        print("\n✨ Features:")
        print("  - Auto-detects app from your command")
        print("  - Auto-logins using credentials from .env")
        print("  - Handles complex 20-step workflows")
        print("  - Works with any website (not just supported apps)")
        print("\n⚙️  Setup Credentials:")
        print("  Add to .env file:")
        print("    {APP_NAME}_EMAIL=your@email.com")
        print("    {APP_NAME}_PASSWORD=yourpassword")
        print("="*70)

    async def stop(self):
        """Stop the browser and cleanup."""
        if self.browser:
            print("\n⏳ Closing browser...")
            await self.browser.stop()
            print("✅ Browser closed")
        else:
            print("\n👋 Goodbye!")


async def main():
    """Main entry point."""
    chat_agent = WebAutomationAgent()

    try:
        # Start and show welcome
        success = await chat_agent.start()
        if not success:
            return

        # Run chat loop
        await chat_agent.chat_loop()

    finally:
        # Cleanup
        await chat_agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
