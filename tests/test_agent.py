"""Tests for the documentation agent."""
import pytest
import asyncio
from pathlib import Path
from src.main import DocumentationAgent


@pytest.mark.asyncio
async def test_agent_initialization():
    """Test that agent initializes correctly."""
    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    assert agent.llm_provider == "claude"
    assert agent.model == "claude-sonnet-4-20250514"


@pytest.mark.asyncio
async def test_simple_navigation():
    """Test simple navigation task."""
    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    result = await agent.document_task(
        question="Navigate to the about page",
        app_url="https://www.example.com",
        max_steps=5
    )

    assert "success" in result
    assert "steps" in result


def test_config_loading():
    """Test that configuration loads correctly."""
    config_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    assert config_path.exists()

    import yaml
    with open(config_path) as f:
        config = yaml.safe_load(f)

    assert "llm" in config
    assert "browser" in config
    assert "detection" in config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
