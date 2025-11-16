"""Tests for browser controller."""
import pytest
from src.browser.controller import BrowserController
from src.browser.som_marker import SoMMarker


@pytest.mark.asyncio
async def test_browser_start_stop():
    """Test browser starts and stops correctly."""
    controller = BrowserController()

    await controller.start()
    assert controller.browser is not None
    assert controller.page is not None

    await controller.stop()


@pytest.mark.asyncio
async def test_som_marker():
    """Test Set-of-Mark element marking."""
    controller = BrowserController()
    await controller.start()

    try:
        await controller.navigate("https://www.example.com")

        # Mark page
        elements = await controller.som_marker.mark_page(controller.page)

        assert len(elements) > 0
        assert elements[0]["marker_id"] == 0

    finally:
        await controller.stop()


def test_som_marker_config():
    """Test SoM marker configuration."""
    config = {
        "background_color": "#00FF00",
        "text_color": "#000000",
        "font_size": 14
    }

    marker = SoMMarker(config)
    assert marker.config["background_color"] == "#00FF00"
    assert marker.config["font_size"] == 14


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
