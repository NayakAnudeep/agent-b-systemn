"""Enhanced detection for Single Page Applications (SPAs)."""
import asyncio
from typing import Optional
from loguru import logger


class SPADetector:
    """Detects and handles SPA-specific UI states."""

    def __init__(self, page):
        """
        Initialize SPA detector.

        Args:
            page: Playwright page object
        """
        self.page = page

    async def wait_for_spa_ready(self, timeout: int = 10000) -> bool:
        """
        Wait for SPA to be fully rendered and ready.

        This handles:
        - React/Vue/Angular rendering
        - Loading spinners
        - Skeleton screens
        - Lazy-loaded content

        Args:
            timeout: Maximum time to wait in milliseconds

        Returns:
            bool: True if SPA appears ready
        """
        logger.debug("Waiting for SPA to be ready...")

        try:
            # Wait for common loading indicators to disappear
            await self._wait_for_loaders_hidden(timeout=5000)

            # Wait for framework to be idle
            await self._wait_for_framework_idle()

            # Wait for animations to complete
            await asyncio.sleep(0.5)

            # Final network idle check
            await self.page.wait_for_load_state("networkidle", timeout=3000)

            logger.debug("SPA appears ready")
            return True

        except Exception as e:
            logger.warning(f"SPA ready check timed out (may be ok): {e}")
            return False

    async def _wait_for_loaders_hidden(self, timeout: int = 5000):
        """Wait for loading spinners and skeleton screens to disappear."""
        logger.debug("Checking for loading indicators...")

        # Common loading indicator selectors
        loader_selectors = [
            '.loading',
            '.loader',
            '.spinner',
            '.loading-spinner',
            '[class*="loading"]',
            '[class*="spinner"]',
            '[data-testid*="loading"]',
            '[aria-label*="loading" i]',
            '.skeleton',
            '[class*="skeleton"]',
            # Linear-specific
            '[class*="Spinner"]',
            # Notion-specific
            '[class*="Loading"]',
        ]

        for selector in loader_selectors:
            try:
                # Check if loader exists and is visible
                loader = self.page.locator(selector).first
                if await loader.is_visible(timeout=500):
                    logger.debug(f"Found loader: {selector}, waiting for it to hide...")
                    await loader.wait_for(state="hidden", timeout=timeout)
                    logger.debug(f"Loader hidden: {selector}")
            except Exception:
                # Loader not found or already hidden
                continue

    async def _wait_for_framework_idle(self):
        """Wait for JavaScript frameworks (React, Vue, Angular) to be idle."""
        logger.debug("Waiting for framework to be idle...")

        await self.page.evaluate("""
            async () => {
                // Wait for requestIdleCallback (if available)
                if (window.requestIdleCallback) {
                    await new Promise(resolve => {
                        requestIdleCallback(resolve, { timeout: 1000 });
                    });
                }

                // Wait for React to finish rendering (if React is present)
                if (window.React || document.querySelector('[data-reactroot]')) {
                    await new Promise(resolve => setTimeout(resolve, 300));
                }

                // Wait for Vue to finish rendering (if Vue is present)
                if (window.Vue) {
                    await new Promise(resolve => setTimeout(resolve, 300));
                }

                // Wait for Angular zone to be stable (if Angular is present)
                if (window.ng) {
                    await new Promise(resolve => setTimeout(resolve, 300));
                }

                // General stability wait
                await new Promise(resolve => setTimeout(resolve, 200));
            }
        """)

    async def detect_modal_opened(self) -> bool:
        """
        Detect if a modal/dialog has opened.

        Returns:
            bool: True if modal detected
        """
        modal_detected = await self.page.evaluate("""
            () => {
                // Check for common modal patterns
                const modalSelectors = [
                    '[role="dialog"]',
                    '[role="alertdialog"]',
                    '.modal',
                    '[class*="Modal"]',
                    '[class*="dialog"]',
                    '[class*="Dialog"]',
                    '[aria-modal="true"]',
                    // Linear-specific
                    '[class*="Sheet"]',
                    '[class*="Popover"]',
                    // Notion-specific
                    '[class*="overlay"]'
                ];

                for (const selector of modalSelectors) {
                    const modal = document.querySelector(selector);
                    if (modal) {
                        const style = window.getComputedStyle(modal);
                        const isVisible = (
                            style.display !== 'none' &&
                            style.visibility !== 'hidden' &&
                            style.opacity !== '0'
                        );

                        if (isVisible) {
                            return true;
                        }
                    }
                }

                // Check for overlay/backdrop (indicates modal)
                const overlaySelectors = [
                    '.overlay',
                    '.backdrop',
                    '[class*="Overlay"]',
                    '[class*="Backdrop"]',
                    '[class*="backdrop"]'
                ];

                for (const selector of overlaySelectors) {
                    const overlay = document.querySelector(selector);
                    if (overlay) {
                        const style = window.getComputedStyle(overlay);
                        if (style.display !== 'none' && style.opacity !== '0') {
                            return true;
                        }
                    }
                }

                return false;
            }
        """)

        if modal_detected:
            logger.info("Modal/dialog detected on page")

        return modal_detected

    async def detect_toast_notification(self) -> bool:
        """
        Detect if a toast/notification has appeared.

        Returns:
            bool: True if toast detected
        """
        toast_detected = await self.page.evaluate("""
            () => {
                const toastSelectors = [
                    '[role="status"]',
                    '[role="alert"]',
                    '.toast',
                    '.notification',
                    '[class*="Toast"]',
                    '[class*="Notification"]',
                    '[class*="snackbar"]',
                    '[class*="Snackbar"]',
                    // Linear-specific
                    '[class*="Banner"]',
                ];

                for (const selector of toastSelectors) {
                    const toast = document.querySelector(selector);
                    if (toast) {
                        const style = window.getComputedStyle(toast);
                        if (style.display !== 'none' && style.opacity !== '0') {
                            return true;
                        }
                    }
                }

                return false;
            }
        """)

        if toast_detected:
            logger.debug("Toast notification detected")

        return toast_detected

    async def wait_for_animation_complete(self, element_selector: Optional[str] = None):
        """
        Wait for CSS animations and transitions to complete.

        Args:
            element_selector: Specific element to watch (or whole document)
        """
        logger.debug("Waiting for animations to complete...")

        await self.page.evaluate("""
            (selector) => {
                return new Promise(resolve => {
                    const element = selector ?
                        document.querySelector(selector) :
                        document.body;

                    if (!element) {
                        resolve();
                        return;
                    }

                    // Check for ongoing animations
                    const animations = element.getAnimations();
                    if (animations.length === 0) {
                        resolve();
                        return;
                    }

                    // Wait for all animations to finish
                    Promise.all(
                        animations.map(animation => animation.finished)
                    ).then(resolve);

                    // Timeout after 2 seconds
                    setTimeout(resolve, 2000);
                });
            }
        """, element_selector)

    async def detect_route_change(self, previous_path: str) -> bool:
        """
        Detect if SPA route has changed (without full page navigation).

        Args:
            previous_path: Previous URL path

        Returns:
            bool: True if route changed
        """
        current_url = self.page.url
        current_path = current_url.split('?')[0]  # Remove query params

        changed = current_path != previous_path

        if changed:
            logger.info(f"SPA route changed: {previous_path} → {current_path}")

        return changed

    async def wait_for_element_stable(
        self,
        selector: str,
        timeout: int = 5000,
        check_interval: int = 300
    ) -> bool:
        """
        Wait for an element to stop moving/changing.

        Useful for:
        - Animated elements settling
        - Dynamic content loading
        - Transitions completing

        Args:
            selector: CSS selector for element
            timeout: Maximum wait time in ms
            check_interval: Time between checks in ms

        Returns:
            bool: True if element is stable
        """
        logger.debug(f"Waiting for element to stabilize: {selector}")

        try:
            stable = await self.page.evaluate("""
                async ({selector, timeout, checkInterval}) => {
                    const element = document.querySelector(selector);
                    if (!element) return false;

                    const startTime = Date.now();
                    let lastRect = element.getBoundingClientRect();
                    let lastHTML = element.innerHTML;
                    let stableCount = 0;

                    while (Date.now() - startTime < timeout) {
                        await new Promise(r => setTimeout(r, checkInterval));

                        const currentRect = element.getBoundingClientRect();
                        const currentHTML = element.innerHTML;

                        const positionStable = (
                            currentRect.top === lastRect.top &&
                            currentRect.left === lastRect.left &&
                            currentRect.width === lastRect.width &&
                            currentRect.height === lastRect.height
                        );

                        const contentStable = currentHTML === lastHTML;

                        if (positionStable && contentStable) {
                            stableCount++;
                            if (stableCount >= 2) {  // Stable for 2 consecutive checks
                                return true;
                            }
                        } else {
                            stableCount = 0;
                        }

                        lastRect = currentRect;
                        lastHTML = currentHTML;
                    }

                    return stableCount >= 1;  // At least somewhat stable
                }
            """, {"selector": selector, "timeout": timeout, "checkInterval": check_interval})

            if stable:
                logger.debug(f"Element is stable: {selector}")
            else:
                logger.debug(f"Element stability timeout: {selector}")

            return stable

        except Exception as e:
            logger.warning(f"Element stability check failed: {e}")
            return False
