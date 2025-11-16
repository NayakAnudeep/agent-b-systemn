"""Set-of-Mark (SoM) implementation for marking interactive elements."""
import json
from typing import Optional
from loguru import logger


class SoMMarker:
    """Manages Set-of-Mark element marking on web pages."""

    def __init__(self, config: Optional[dict] = None):
        """Initialize SoM marker with configuration."""
        self.config = config or {
            "background_color": "#FF0000",
            "text_color": "#FFFFFF",
            "font_size": 12,
            "padding": "2px 6px",
            "z_index": 10000
        }

    async def mark_page(self, page) -> list[dict]:
        """
        Inject numbered markers on interactive elements and return element info.

        Args:
            page: Playwright page object

        Returns:
            List of dictionaries containing element information
        """
        logger.info("Marking page with Set-of-Mark overlays")

        # JavaScript to inject markers and collect element information
        marker_script = """
        () => {
            // Remove any existing markers
            document.querySelectorAll('.som-marker').forEach(el => el.remove());

            // Define selectors for interactive elements
            const selectors = [
                'button',
                'a[href]',
                'input:not([type="hidden"])',
                'textarea',
                'select',
                '[role="button"]',
                '[role="link"]',
                '[role="tab"]',
                '[role="menuitem"]',
                '[onclick]',
                '[contenteditable="true"]',
                // Additional selectors for modern React apps like Notion
                'div[class*="button"]',
                'div[class*="Button"]',
                'span[class*="button"]',
                '[class*="clickable"]',
                '[class*="interactive"]',
                '[data-clickable="true"]'
            ];

            const elements = Array.from(
                document.querySelectorAll(selectors.join(','))
            );

            // Filter for visible and interactive elements
            const visibleElements = elements.filter(el => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);

                return (
                    rect.width > 0 &&
                    rect.height > 0 &&
                    style.visibility !== 'hidden' &&
                    style.display !== 'none' &&
                    style.opacity !== '0'
                );
            });

            // ADDITIONAL: Also mark elements with cursor: pointer (catches modern React buttons)
            const pointerElements = Array.from(document.querySelectorAll('div, span')).filter(el => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);

                return (
                    style.cursor === 'pointer' &&
                    rect.width > 20 &&  // Reasonable minimum size
                    rect.height > 15 &&
                    rect.width < 500 &&  // Not too large (avoid containers)
                    rect.height < 200 &&
                    style.visibility !== 'hidden' &&
                    style.display !== 'none' &&
                    style.opacity !== '0'
                );
            });

            // Merge and deduplicate
            const allInteractive = [...visibleElements, ...pointerElements];
            const uniqueElements = Array.from(new Set(allInteractive));

            // Create markers and collect info
            const elementInfo = [];

            uniqueElements.forEach((el, idx) => {
                // Create marker overlay
                const marker = document.createElement('div');
                marker.className = 'som-marker';
                marker.textContent = idx;
                marker.style.cssText = `
                    position: absolute;
                    background: """ + self.config['background_color'] + """;
                    color: """ + self.config['text_color'] + """;
                    padding: """ + self.config['padding'] + """;
                    border-radius: 3px;
                    font-size: """ + str(self.config['font_size']) + """px;
                    font-weight: bold;
                    font-family: monospace;
                    z-index: """ + str(self.config['z_index']) + """;
                    pointer-events: none;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3);
                `;

                const rect = el.getBoundingClientRect();
                marker.style.top = (window.scrollY + rect.top) + 'px';
                marker.style.left = (window.scrollX + rect.left) + 'px';

                document.body.appendChild(marker);

                // Collect element information
                const info = {
                    marker_id: idx,
                    tag_name: el.tagName.toLowerCase(),
                    text: el.textContent?.trim().substring(0, 100) || null,
                    role: el.getAttribute('role'),
                    aria_label: el.getAttribute('aria-label'),
                    placeholder: el.getAttribute('placeholder'),
                    href: el.getAttribute('href'),
                    type: el.getAttribute('type'),
                    class: el.className,
                    id: el.id
                };

                elementInfo.push(info);
            });

            return elementInfo;
        }
        """

        try:
            elements = await page.evaluate(marker_script)
            logger.info(f"Marked {len(elements)} interactive elements")
            return elements
        except Exception as e:
            logger.error(f"Failed to mark page: {e}")
            return []

    async def remove_markers(self, page):
        """Remove all SoM markers from the page."""
        try:
            await page.evaluate("document.querySelectorAll('.som-marker').forEach(el => el.remove())")
            logger.debug("Removed SoM markers")
        except Exception as e:
            logger.error(f"Failed to remove markers: {e}")

    async def highlight_element(self, page, marker_id: int, color: str = "#00FF00"):
        """Temporarily highlight a specific element."""
        highlight_script = f"""
        (marker_id) => {{
            const markers = document.querySelectorAll('.som-marker');
            if (marker_id < markers.length) {{
                const marker = markers[marker_id];
                marker.style.background = '{color}';
                marker.style.transform = 'scale(1.2)';
                setTimeout(() => {{
                    marker.style.background = '{self.config['background_color']}';
                    marker.style.transform = 'scale(1)';
                }}, 500);
            }}
        }}
        """
        try:
            await page.evaluate(highlight_script, marker_id)
        except Exception as e:
            logger.error(f"Failed to highlight element {marker_id}: {e}")
