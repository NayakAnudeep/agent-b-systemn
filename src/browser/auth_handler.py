"""
Hybrid DOM + Vision Authentication Handler

Combines:
- DOM-based element finding (fast, reliable)
- Vision-based verification (accurate, handles edge cases)
- State tracking (avoids redundant actions)
- Stuck detection (falls back to vision when DOM fails)
"""
import asyncio
import hashlib
from typing import Optional, Dict, Literal
from loguru import logger
from playwright.async_api import Page
from pathlib import Path


class AuthHandler:
    """
    Hybrid authentication handler using both DOM and Vision.

    Flow:
    1. Use DOM selectors to interact (fast)
    2. Track page state changes
    3. If stuck (no state change), fall back to vision
    4. Use vision to verify success
    """

    def __init__(self, vision_agent, page: Page, som_marker=None, action_executor=None):
        """
        Initialize authentication handler.

        Args:
            vision_agent: VisionLoginAgent for verification
            page: Playwright page object
            som_marker: SoMMarker for vision-based actions (optional)
            action_executor: ActionExecutor for vision-based actions (optional)
        """
        self.vision_agent = vision_agent
        self.page = page
        self.som_marker = som_marker
        self.action_executor = action_executor

        # Track what we've done to avoid redundancy
        self.actions_taken = {
            "navigated_to_login": False,
            "filled_email": False,
            "clicked_continue_after_email": False,
            "filled_password": False,
            "submitted_login": False
        }

        # State tracking for stuck detection
        self.previous_state = None
        self.stuck_counter = 0
        self.max_stuck_iterations = 2

        # 2FA detection keywords (includes email verification)
        self.twofa_keywords = [
            # Traditional 2FA
            "two-factor", "2fa", "two factor", "2-factor",
            "verification code", "authenticator", "security code",
            "6-digit", "authentication code", "verify your identity",
            "enter code", "verification", "multi-factor",
            # Email verification / Magic links
            "check your email", "email verification", "sent you an email",
            "sent you a link", "magic link", "click the link",
            "verify your email", "email sent", "we've sent you",
            "check your inbox", "sent a link", "open the email",
            "confirmation email", "verify email address"
        ]

    async def authenticate(
        self,
        credentials: Dict[str, str],
        max_steps: int = 10,
        screenshot_dir: Optional[str] = None
    ) -> bool:
        """
        Main authentication flow.

        Args:
            credentials: Dict with 'email'/'username' and 'password'
            max_steps: Maximum steps to attempt
            screenshot_dir: Where to save screenshots

        Returns:
            bool: True if successfully authenticated
        """
        email = credentials.get('email') or credentials.get('username')
        password = credentials.get('password')

        if not email or not password:
            logger.error("Missing credentials")
            return False

        logger.info(f"🔐 Starting hybrid authentication for {email}")

        for step in range(1, max_steps + 1):
            logger.info(f"Auth step {step}/{max_steps}")

            # Wait for page stability
            await asyncio.sleep(1)

            # Track state changes to detect if stuck
            current_state = await self._get_page_state()
            if current_state == self.previous_state:
                self.stuck_counter += 1
                logger.warning(f"⚠️  Page state unchanged (stuck count: {self.stuck_counter})")
            else:
                self.stuck_counter = 0  # Reset if state changed
                self.previous_state = current_state

            # Mark page with SoM BEFORE screenshot for vision
            elements = []
            if self.som_marker:
                await self.som_marker.mark_page(self.page)

            # Take screenshot WITH markers visible
            screenshot_path = await self._take_screenshot(screenshot_dir, step)

            # Get current state from vision
            current_url = self.page.url

            vision_state = self.vision_agent.decide_login_action(
                screenshot_path=screenshot_path,
                credentials=credentials,
                elements=elements,
                current_url=current_url
            )

            # Clear markers after vision analysis
            if self.som_marker:
                await self.som_marker.remove_markers(self.page)

            # Check if already logged in
            if vision_state.get("is_logged_in", False):
                logger.info("✅ Successfully authenticated!")
                return True

            # If stuck for too long, use vision to decide action
            if self.stuck_counter >= self.max_stuck_iterations:
                logger.warning(f"🔄 Stuck detected! Falling back to vision-based action")
                success = await self._vision_fallback_action(vision_state, screenshot_path)
                if success:
                    self.stuck_counter = 0  # Reset after successful action
                    await asyncio.sleep(2)
                    continue

            # ALWAYS try to navigate to login page first (before filling any fields)
            # This prevents filling signup fields on landing pages
            if not self.actions_taken["navigated_to_login"]:
                is_login_page = vision_state.get("is_login_page", False)

                if is_login_page:
                    # Already on the login page
                    logger.info("✓ Already on login page")
                    self.actions_taken["navigated_to_login"] = True
                    continue
                else:
                    # Not on login page - need to navigate to it
                    # First try DOM selectors (fast)
                    if await self._navigate_to_login_page():
                        self.actions_taken["navigated_to_login"] = True
                        logger.info("✓ Navigated to login page via DOM")
                        await asyncio.sleep(2)
                        continue

                    # DOM failed - use vision agent's recommendation
                    logger.info("DOM failed to find Sign in button - using vision agent")
                    action = vision_state.get("action")
                    if action and action.action_type == "click":
                        # Vision agent wants us to click something (likely "Sign in")
                        logger.info(f"Vision recommends: click - {action.step_description}")
                        success = await self._vision_fallback_action(vision_state, screenshot_path)
                        if success:
                            self.actions_taken["navigated_to_login"] = True
                            logger.info("✓ Navigated to login page via vision")
                            await asyncio.sleep(2)
                            continue

                    logger.warning("⚠️  Failed to navigate to login page")

            # Now we should be on login page - start filling form

            # Step 1: Fill email if not done
            if not self.actions_taken["filled_email"]:
                if await self._fill_email_field(email):
                    self.actions_taken["filled_email"] = True
                    logger.info("✓ Email filled")
                    await asyncio.sleep(0.5)
                continue  # Go to next iteration to click Continue

            # Step 2: Click Continue after email (MUST succeed before moving to password)
            # BUT: Skip if password field is already visible (single-page login like GitHub)
            if not self.actions_taken["clicked_continue_after_email"]:
                # Check if password field is already visible (single-page login)
                password_visible = await self._is_password_field_visible()

                if password_visible:
                    # Single-page login (email + password on same page)
                    logger.info("✓ Password field already visible - skipping Continue button")
                    self.actions_taken["clicked_continue_after_email"] = True
                    continue

                # Multi-step login - need to click Continue
                continue_clicked = await self._click_continue_button()

                if continue_clicked:
                    logger.info("✓ Continue button clicked via DOM")
                    self.actions_taken["clicked_continue_after_email"] = True
                    await asyncio.sleep(2)

                    # Check for email verification page (Linear, Slack, etc. show it here)
                    if await self._detect_2fa_page():
                        logger.info("🔐 Email verification detected after entering email - waiting for human")
                        success = await self.wait_for_human_intervention(max_wait_seconds=300)
                        if success:
                            logger.info("✅ User completed email verification - authentication successful")
                            return True  # Email verification = successful login for these apps
                        else:
                            logger.error("❌ Email verification timeout or failed")
                            return False

                    continue
                else:
                    # DOM couldn't find Continue - use vision fallback
                    logger.warning("⚠️  DOM couldn't find Continue button, using vision fallback")
                    if await self._vision_fallback_action(vision_state, screenshot_path):
                        logger.info("✓ Vision action executed")
                        self.actions_taken["clicked_continue_after_email"] = True
                        await asyncio.sleep(2)

                        # Check for email verification page here too
                        if await self._detect_2fa_page():
                            logger.info("🔐 Email verification detected - waiting for human")
                            success = await self.wait_for_human_intervention(max_wait_seconds=300)
                            if success:
                                logger.info("✅ User completed email verification - authentication successful")
                                return True
                            else:
                                logger.error("❌ Email verification timeout or failed")
                                return False

                        continue
                    else:
                        logger.warning("⚠️  Both DOM and vision failed to click Continue")
                        await asyncio.sleep(1)
                        continue  # Keep trying in next iteration

            # Step 3: Fill password (only after Continue was clicked)
            if not self.actions_taken["filled_password"]:
                if await self._fill_password_field(password):
                    self.actions_taken["filled_password"] = True
                    logger.info("✓ Password filled")
                    await asyncio.sleep(0.5)
                continue  # Go to next iteration to submit

            # Step 4: Submit login form
            if not self.actions_taken["submitted_login"]:
                if await self._submit_login_form():
                    logger.info("✓ Login form submitted")
                    self.actions_taken["submitted_login"] = True
                    await asyncio.sleep(3)  # Wait for auth to process

                    # Check if 2FA page appeared
                    if await self._detect_2fa_page():
                        logger.info("🔐 2FA page detected - waiting for human intervention")
                        success = await self.wait_for_human_intervention(max_wait_seconds=300)
                        if success:
                            logger.info("✅ User completed 2FA - continuing authentication check")
                            # Continue to check if logged in
                        else:
                            logger.error("❌ 2FA timeout or failed")
                            return False

            # Check for errors
            error_msg = await self._check_for_error_messages()
            if error_msg:
                logger.error(f"❌ Login error: {error_msg}")
                # Reset actions to retry
                self._reset_actions()
                await asyncio.sleep(2)

        logger.error(f"❌ Authentication failed after {max_steps} steps")
        return False

    async def _navigate_to_login_page(self) -> bool:
        """Find and click 'Log in' button to get to login page."""
        logger.debug("Looking for login button...")

        # Priority order: exact text matches first, then href patterns
        # Explicitly filter out "Sign up" to avoid clicking wrong button
        selectors = [
            'a:has-text("Sign in"):not(:has-text("Sign up"))',
            'a:has-text("Log in"):not(:has-text("Sign up"))',
            'button:has-text("Sign in"):not(:has-text("Sign up"))',
            'button:has-text("Log in"):not(:has-text("Sign up"))',
            'a:has-text("Login"):not(:has-text("Sign up"))',
            'button:has-text("Login"):not(:has-text("Sign up"))',
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    # Double-check it's not a signup link
                    text = await element.inner_text()
                    text_lower = text.lower()
                    if 'sign up' in text_lower or 'signup' in text_lower or 'register' in text_lower:
                        logger.debug(f"Skipping signup link: {text}")
                        continue

                    await element.click()
                    logger.debug(f"Clicked login button: {selector} (text: {text})")
                    return True
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")

        # Fallback: try href patterns (but still filter out signup)
        href_selectors = [
            '[href*="/login"]:not([href*="sign"])',
            '[href*="/signin"]:not([href*="signup"])',
        ]

        for selector in href_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    text = await element.inner_text()
                    if 'sign up' not in text.lower() and 'signup' not in text.lower():
                        await element.click()
                        logger.debug(f"Clicked login link: {selector}")
                        return True
            except Exception as e:
                logger.debug(f"Fallback selector {selector} failed: {e}")

        return False

    async def _fill_email_field(self, email: str) -> bool:
        """Fill email field using DOM."""
        logger.debug("Filling email field...")

        selectors = [
            'input[type="email"]',
            'input[name="email"]',
            'input[placeholder*="email" i]',
            'input[autocomplete="email"]',
            'input[autocomplete="username"]',
            'input[id*="email" i]',
            'input[name="username"]'
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    # Clear any existing value
                    await element.click()
                    await self.page.keyboard.press('Control+A')
                    await element.fill(email)
                    logger.debug(f"Email filled via: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")

        return False

    async def _is_password_field_visible(self) -> bool:
        """Check if password field is visible (indicates single-page login)."""
        try:
            selectors = [
                'input[type="password"]',
                'input[autocomplete="current-password"]',
                'input[name="password"]',
                'input[id*="password"]'
            ]

            for selector in selectors:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    logger.debug(f"Password field found: {selector}")
                    return True

            return False
        except Exception as e:
            logger.debug(f"Error checking for password field: {e}")
            return False

    async def _click_continue_button(self) -> bool:
        """Click Continue/Next button after email entry."""
        logger.debug("Looking for Continue button...")

        selectors = [
            'button:has-text("Continue")',
            'button:has-text("Next")',
            'button:has-text("Continue with email")',
            'button[type="submit"]:visible'
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    await element.click()
                    logger.debug(f"Clicked continue: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")

        return False

    async def _fill_password_field(self, password: str) -> bool:
        """Fill password field using DOM."""
        logger.debug("Filling password field...")

        selectors = [
            'input[type="password"]',
            'input[name="password"]',
            'input[autocomplete="current-password"]',
            'input[id*="password" i]'
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    # CRITICAL: Clear any autofilled password
                    await element.click()
                    await asyncio.sleep(0.2)

                    # Select all and clear
                    await self.page.keyboard.press('Control+A')
                    await asyncio.sleep(0.1)
                    await self.page.keyboard.press('Backspace')
                    await asyncio.sleep(0.1)

                    # Type password
                    await element.fill(password)
                    logger.debug(f"Password filled via: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")

        return False

    async def _submit_login_form(self) -> bool:
        """Submit the login form."""
        logger.debug("Submitting login form...")

        # Try clicking submit button
        selectors = [
            'button:has-text("Continue with password")',
            'button:has-text("Log in")',
            'button:has-text("Sign in")',
            'button:has-text("Continue")',
            'button[type="submit"]:visible',
            'input[type="submit"]'
        ]

        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    await element.click()
                    logger.debug(f"Submitted via: {selector}")
                    return True
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")

        # Fallback: Press Enter in password field
        try:
            pwd_field = await self.page.query_selector('input[type="password"]')
            if pwd_field and await pwd_field.is_visible():
                await pwd_field.press('Enter')
                logger.debug("Submitted via Enter key")
                return True
        except Exception as e:
            logger.debug(f"Enter submit failed: {e}")

        return False

    async def _check_for_error_messages(self) -> Optional[str]:
        """Check if there are any error messages on the page."""
        error_selectors = [
            'text="Incorrect password"',
            'text="Invalid email"',
            'text="Invalid credentials"',
            'text="Login failed"',
            '[role="alert"]',
            '.error',
            '.error-message',
            '[class*="error" i]'
        ]

        for selector in error_selectors:
            try:
                element = await self.page.query_selector(selector)
                if element and await element.is_visible():
                    text = await element.inner_text()
                    return text.strip()
            except:
                continue

        return None

    async def _take_screenshot(self, screenshot_dir: Optional[str], step: int) -> str:
        """Take screenshot for vision analysis."""
        if screenshot_dir:
            path = Path(screenshot_dir) / f"auth_step_{step}.png"
        else:
            path = Path(f"/tmp/auth_step_{step}.png")

        await self.page.screenshot(path=str(path))
        return str(path)

    def _reset_actions(self):
        """Reset action tracking (for retry after error)."""
        self.actions_taken = {
            "navigated_to_login": True,  # Don't re-navigate
            "filled_email": False,
            "clicked_continue_after_email": False,
            "filled_password": False,
            "submitted_login": False
        }

    async def _get_page_state(self) -> str:
        """Get current page state as hash (URL + content)."""
        try:
            url = self.page.url
            # Get page content for hashing
            content = await self.page.content()
            # Create hash of URL + content
            state_string = f"{url}:{content[:500]}"  # First 500 chars to detect changes
            return hashlib.md5(state_string.encode()).hexdigest()
        except Exception as e:
            logger.debug(f"Failed to get page state: {e}")
            return ""

    async def _vision_fallback_action(self, vision_state: Dict, screenshot_path: str) -> bool:
        """
        Execute action recommended by vision when DOM is stuck.

        Args:
            vision_state: Decision from vision agent
            screenshot_path: Path to screenshot for SoM

        Returns:
            bool: True if action executed successfully
        """
        if not self.som_marker or not self.action_executor:
            logger.error("Cannot use vision fallback - SoM/ActionExecutor not provided")
            return False

        try:
            action = vision_state.get("action")
            if not action:
                logger.warning("No action in vision state")
                return False

            logger.info(f"Vision recommends: {action.action_type} - {action.step_description}")

            # Mark the page with SoM
            await self.som_marker.mark_page(self.page)

            # Execute the vision-recommended action
            success = await self.action_executor.execute(action)

            # Clear markers
            await self.som_marker.remove_markers(self.page)

            return success
        except Exception as e:
            logger.error(f"Vision fallback action failed: {e}")
            return False

    async def _detect_2fa_page(self) -> bool:
        """
        Detect if current page is a 2FA/MFA verification page.

        Returns:
            bool: True if 2FA page detected
        """
        try:
            # Get page content
            content = await self.page.content()
            title = await self.page.title()
            url = self.page.url

            # Combine all text for checking
            all_text = f"{content} {title} {url}".lower()

            # Check for 2FA keywords
            for keyword in self.twofa_keywords:
                if keyword.lower() in all_text:
                    logger.info(f"🔐 2FA detected (keyword: '{keyword}')")
                    return True

            return False
        except Exception as e:
            logger.error(f"Error detecting 2FA: {e}")
            return False

    async def wait_for_human_intervention(self, max_wait_seconds: int = 300):
        """
        Pause and wait for human to complete 2FA manually.
        Monitors page state and resumes when state changes.

        Args:
            max_wait_seconds: Maximum time to wait (default: 5 minutes)

        Returns:
            bool: True if state changed (user completed 2FA), False if timeout
        """
        logger.info("⏸️  Pausing for human intervention (2FA/Email verification detected)")
        print("\n" + "="*70)
        print("🔐 VERIFICATION REQUIRED (2FA / EMAIL)")
        print("="*70)
        print("\n⏸️  The agent has detected a verification page.")
        print("📱 Please complete the verification manually in the browser:")
        print("   • Check your email and click the verification link")
        print("   • Enter your authentication code")
        print("   • Complete SMS verification")
        print("   • Approve the login on your device")
        print("\n💡 The agent will automatically resume once you complete verification.")
        print(f"⏱️  Waiting up to {max_wait_seconds} seconds...")
        print("="*70 + "\n")

        # Get initial state
        initial_state = await self._get_page_state()
        initial_url = self.page.url

        start_time = asyncio.get_event_loop().time()
        check_interval = 2  # Check every 2 seconds

        while True:
            # Check if timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed > max_wait_seconds:
                logger.warning(f"⏱️  Timeout waiting for 2FA ({max_wait_seconds}s)")
                print(f"\n⚠️  Timeout after {max_wait_seconds} seconds")
                return False

            # Wait before checking
            await asyncio.sleep(check_interval)

            # Check if state changed
            current_state = await self._get_page_state()
            current_url = self.page.url

            # State changed = user completed 2FA
            if current_state != initial_state or current_url != initial_url:
                logger.info("✅ Page state changed - resuming automation")
                print("\n✅ 2FA completed! Resuming automation...")
                print("-" * 70 + "\n")
                return True

            # Show progress
            remaining = max_wait_seconds - int(elapsed)
            if int(elapsed) % 10 == 0:  # Update every 10 seconds
                print(f"⏳ Still waiting... ({remaining}s remaining)")

        return False
