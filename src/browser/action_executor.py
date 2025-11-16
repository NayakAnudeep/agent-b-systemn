"""Executes web automation actions on Playwright pages."""
import asyncio
from typing import Optional
from loguru import logger
from src.agent.schemas import AgentAction


class ActionExecutor:
    """Handles execution of web automation actions."""

    def __init__(self, page, som_marker):
        """
        Initialize action executor.

        Args:
            page: Playwright page object
            som_marker: SoMMarker instance for element interaction
        """
        self.page = page
        self.som_marker = som_marker

    async def _get_element_by_marker(self, marker_id: int):
        """
        Get Playwright ElementHandle by marker ID.

        Args:
            marker_id: The marker index (0-based)

        Returns:
            ElementHandle or None if not found
        """
        # Use JavaScript to get the same elements as SoM marking (including cursor: pointer detection)
        get_element_script = """
        (marker_id) => {
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

            // Also get cursor: pointer elements
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

            return uniqueElements[marker_id] || null;
        }
        """

        try:
            element_handle = await self.page.evaluate_handle(get_element_script, marker_id)
            # Convert JSHandle to ElementHandle
            if element_handle:
                return element_handle.as_element()
            return None
        except Exception as e:
            logger.debug(f"Could not get element by marker {marker_id}: {e}")
            return None

    async def execute(self, action: AgentAction) -> bool:
        """
        Execute an agent action.

        Args:
            action: AgentAction to execute

        Returns:
            bool: True if action succeeded, False otherwise
        """
        logger.info(f"Executing action: {action.action_type} - {action.step_description}")

        try:
            if action.action_type == "click":
                return await self._execute_click(action)
            elif action.action_type == "type":
                return await self._execute_type(action)
            elif action.action_type == "navigate":
                return await self._execute_navigate(action)
            elif action.action_type == "wait":
                return await self._execute_wait(action)
            elif action.action_type == "scroll":
                return await self._execute_scroll(action)
            elif action.action_type == "done":
                logger.info("Task marked as complete")
                return True
            else:
                logger.error(f"Unknown action type: {action.action_type}")
                return False

        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return False

    async def _try_click_marker(self, marker_id: int) -> bool:
        """
        Try to click element at given marker ID.

        Args:
            marker_id: The marker index to click

        Returns:
            bool: True if click succeeded, False otherwise
        """
        try:
            # First try: Use Playwright's native click (most reliable for React apps)
            element = await self._get_element_by_marker(marker_id)
            if element:
                try:
                    # Playwright's click handles all events properly
                    await element.click(force=True, timeout=2000)
                    logger.debug(f"Playwright native click succeeded on marker [{marker_id}]")
                    return True
                except Exception as e:
                    logger.debug(f"Playwright click failed: {e}, trying JavaScript fallback")

            # Second try: JavaScript click with MouseEvent dispatch
            click_script = """
            (marker_id) => {
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

                // Also get cursor: pointer elements
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

                if (marker_id < uniqueElements.length) {
                    const element = uniqueElements[marker_id];

                    // Try multiple click methods for maximum compatibility
                    // 1. Dispatch real mouse events (works with React synthetic events)
                    const rect = element.getBoundingClientRect();
                    const x = rect.left + rect.width / 2;
                    const y = rect.top + rect.height / 2;

                    ['mousedown', 'mouseup', 'click'].forEach(eventType => {
                        const event = new MouseEvent(eventType, {
                            view: window,
                            bubbles: true,
                            cancelable: true,
                            clientX: x,
                            clientY: y
                        });
                        element.dispatchEvent(event);
                    });

                    // 2. Also trigger the native click for good measure
                    element.click();

                    return true;
                }
                return false;
            }
            """
            result = await self.page.evaluate(click_script, marker_id)
            return result
        except Exception as e:
            logger.debug(f"Failed to click marker [{marker_id}]: {e}")
            return False

    async def _execute_click(self, action: AgentAction) -> bool:
        """Execute a click action with fallback to adjacent markers."""
        if not action.target:
            logger.error("Click action requires a target")
            return False

        # Parse marker ID if target is like "[15]"
        if action.target.startswith("[") and action.target.endswith("]"):
            try:
                marker_id = int(action.target[1:-1])
                await self.som_marker.highlight_element(self.page, marker_id)

                # Validate element type matches intent (e.g., don't click password field when looking for button)
                element = await self._get_element_by_marker(marker_id)
                if element:
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    element_type = await element.get_attribute("type")

                    # If action description mentions "button" or "continue" but element is input field, try next marker
                    action_desc_lower = action.step_description.lower() if action.step_description else ""
                    if ("button" in action_desc_lower or "continue" in action_desc_lower):
                        if tag_name == "input" and element_type in ["password", "text", "email"]:
                            logger.warning(f"Marker [{marker_id}] is a {element_type} input, not a button. Trying next marker...")
                            marker_id += 1
                            logger.info(f"Trying marker [{marker_id}] instead")

                # Try the requested marker (possibly adjusted)
                if await self._try_click_marker(marker_id):
                    logger.info(f"Clicked element at marker [{marker_id}]")
                    await asyncio.sleep(0.5)
                    return True

                # Fallback: try adjacent markers (common when elements overlap)
                logger.warning(f"Marker [{marker_id}] failed, trying adjacent markers...")

                # Try marker_id + 1
                if await self._try_click_marker(marker_id + 1):
                    logger.info(f"Successfully clicked adjacent marker [{marker_id + 1}]")
                    await asyncio.sleep(0.5)
                    return True

                # Try marker_id - 1
                if marker_id > 0 and await self._try_click_marker(marker_id - 1):
                    logger.info(f"Successfully clicked adjacent marker [{marker_id - 1}]")
                    await asyncio.sleep(0.5)
                    return True

                logger.error(f"Element at marker [{marker_id}] and adjacent markers not found")
                return False

            except ValueError:
                logger.error(f"Invalid marker ID format: {action.target}")
                return False
        else:
            # Fallback: Target is descriptive text, not a marker ID
            # This happens when vision agent couldn't identify the marker
            logger.warning(f"Non-standard target format: {action.target}")
            logger.error(f"Vision agent returned descriptive target instead of marker ID: {action.target}")
            logger.error(f"Cannot execute click without marker ID. Vision agent should specify target like '[49]'")
            return False

    async def _execute_type(self, action: AgentAction) -> bool:
        """Execute a type action using Playwright's native fill method."""
        if not action.target or not action.value:
            logger.error("Type action requires both target and value")
            return False

        # Parse marker ID
        if action.target.startswith("[") and action.target.endswith("]"):
            try:
                marker_id = int(action.target[1:-1])

                # Get element handle using Playwright
                element = await self._get_element_by_marker(marker_id)

                if element:
                    # Validate it's a typeable element (not a checkbox/radio)
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    element_type = await element.get_attribute("type")

                    # Skip checkboxes and radio buttons
                    if element_type in ["checkbox", "radio", "submit", "button"]:
                        logger.warning(f"Marker [{marker_id}] is a {element_type} input, searching for text input nearby...")

                        # Try to find a text input nearby (next few markers)
                        for offset in range(1, 5):
                            alt_marker = marker_id + offset
                            alt_element = await self._get_element_by_marker(alt_marker)
                            if alt_element:
                                alt_type = await alt_element.get_attribute("type")
                                alt_tag = await alt_element.evaluate("el => el.tagName.toLowerCase()")
                                if alt_tag in ["input", "textarea"] and alt_type not in ["checkbox", "radio", "submit", "button"]:
                                    logger.info(f"Found text input at marker [{alt_marker}]")
                                    element = alt_element
                                    marker_id = alt_marker
                                    break

                    # Highlight the element
                    await self.som_marker.highlight_element(self.page, marker_id)

                    # Check if element is contenteditable or in a rich text editor
                    is_contenteditable = await element.evaluate("""
                        el => {
                            // Direct contenteditable check
                            if (el.isContentEditable || el.getAttribute('contenteditable') === 'true') {
                                return true;
                            }

                            // Check for Notion-specific attributes
                            if (el.hasAttribute('data-content-editable-leaf') ||
                                el.hasAttribute('data-block-id') ||
                                el.className?.includes('notion-') ||
                                el.closest('[contenteditable="true"]')) {
                                return true;
                            }

                            // Check if it's a div with role textbox (rich editors)
                            if (el.tagName === 'DIV' && el.getAttribute('role') === 'textbox') {
                                return true;
                            }

                            return false;
                        }
                    """)

                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")

                    if is_contenteditable or tag_name == "div":
                        # For contenteditable or div elements, use keyboard typing (safer for Notion)
                        logger.debug(f"Element [{marker_id}] is contenteditable/div, using keyboard typing")
                        await element.click()
                        await asyncio.sleep(0.3)

                        # Type the text (no need to clear for empty Notion blocks)
                        await self.page.keyboard.type(action.value, delay=20)
                    else:
                        # For standard inputs (input, textarea), use fill()
                        try:
                            await element.fill(action.value, timeout=5000)
                        except Exception as e:
                            # Fallback to keyboard typing if fill fails
                            logger.warning(f"Fill failed, trying keyboard typing: {e}")
                            await element.click()
                            await asyncio.sleep(0.3)
                            await self.page.keyboard.type(action.value, delay=20)

                    logger.info(f"Typed '{action.value}' into element [{marker_id}]")
                    await asyncio.sleep(0.3)
                    return True
                else:
                    logger.error(f"Element at marker [{marker_id}] not found")
                    return False

            except ValueError:
                logger.error(f"Invalid marker ID format: {action.target}")
                return False
            except Exception as e:
                logger.error(f"Type action failed: {e}")
                return False
        else:
            logger.warning(f"Non-standard target format: {action.target}")
            return False

    async def _execute_navigate(self, action: AgentAction) -> bool:
        """Execute a navigation action."""
        if not action.value:
            logger.error("Navigate action requires a URL value")
            return False

        try:
            await self.page.goto(action.value, wait_until="networkidle", timeout=30000)
            logger.info(f"Navigated to {action.value}")
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False

    async def _execute_wait(self, action: AgentAction) -> bool:
        """Execute a wait action."""
        try:
            await self.page.wait_for_load_state("networkidle", timeout=10000)
            await asyncio.sleep(1)  # Additional stability wait
            logger.info("Wait completed")
            return True
        except Exception as e:
            logger.warning(f"Wait timed out (may be ok): {e}")
            return True  # Don't fail on wait timeout

    async def _execute_scroll(self, action: AgentAction) -> bool:
        """Execute a scroll action."""
        direction = action.scroll_direction or "down"
        pixels = 500 if direction == "down" else -500

        try:
            await self.page.evaluate(f"window.scrollBy(0, {pixels})")
            await asyncio.sleep(0.5)
            logger.info(f"Scrolled {direction}")
            return True
        except Exception as e:
            logger.error(f"Scroll failed: {e}")
            return False
