"""Generates visual step-by-step guides from screenshots."""
import json
from pathlib import Path
from typing import List, Optional
from loguru import logger

from src.screenshot.manager import ScreenshotRecord


class GuideGenerator:
    """Generates documentation guides from screenshot sequences."""

    def __init__(self):
        """Initialize guide generator."""
        pass

    def generate_markdown(
        self,
        screenshots: List[ScreenshotRecord],
        task_goal: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate a markdown guide from screenshots.

        Args:
            screenshots: List of screenshot records
            task_goal: The original task goal
            output_path: Optional path to save the guide

        Returns:
            Markdown content as string
        """
        markdown = f"# Task Guide: {task_goal}\n\n"
        markdown += f"*Generated on {screenshots[0].timestamp if screenshots else 'N/A'}*\n\n"
        markdown += "---\n\n"

        for i, record in enumerate(screenshots, 1):
            markdown += f"## Step {i}: {record.description}\n\n"
            markdown += f"**Action**: {record.action_type}\n\n"

            if record.element_target:
                markdown += f"**Target**: {record.element_target}\n\n"

            # Embed screenshot (relative path)
            screenshot_name = Path(record.path).name
            markdown += f"![Step {i}]({screenshot_name})\n\n"
            markdown += "---\n\n"

        if output_path:
            output_path.write_text(markdown)
            logger.info(f"Markdown guide saved to {output_path}")

        return markdown

    def generate_json(
        self,
        screenshots: List[ScreenshotRecord],
        task_goal: str,
        output_path: Optional[Path] = None
    ) -> dict:
        """
        Generate a JSON guide from screenshots.

        Args:
            screenshots: List of screenshot records
            task_goal: The original task goal
            output_path: Optional path to save the guide

        Returns:
            Dictionary representation
        """
        guide = {
            "task_goal": task_goal,
            "total_steps": len(screenshots),
            "steps": [
                {
                    "step_number": record.step_number,
                    "description": record.description,
                    "action_type": record.action_type,
                    "element_target": record.element_target,
                    "screenshot_path": record.path,
                    "timestamp": record.timestamp
                }
                for record in screenshots
            ]
        }

        if output_path:
            output_path.write_text(json.dumps(guide, indent=2))
            logger.info(f"JSON guide saved to {output_path}")

        return guide

    def generate_html(
        self,
        screenshots: List[ScreenshotRecord],
        task_goal: str,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Generate an HTML guide from screenshots.

        Args:
            screenshots: List of screenshot records
            task_goal: The original task goal
            output_path: Optional path to save the guide

        Returns:
            HTML content as string
        """
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{task_goal}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }}
        .step {{
            margin: 30px 0;
            padding: 20px;
            background: #fafafa;
            border-left: 4px solid #007bff;
            border-radius: 4px;
        }}
        .step h2 {{
            color: #007bff;
            margin-top: 0;
        }}
        .step-meta {{
            color: #666;
            font-size: 14px;
            margin: 10px 0;
        }}
        .step img {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 4px;
            margin-top: 15px;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            background: #007bff;
            color: white;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{task_goal}</h1>
        <p><em>Total steps: {len(screenshots)}</em></p>
"""

        for i, record in enumerate(screenshots, 1):
            screenshot_name = Path(record.path).name
            html += f"""
        <div class="step">
            <h2>Step {i}: {record.description}</h2>
            <div class="step-meta">
                <span class="badge">{record.action_type.upper()}</span>
"""
            if record.element_target:
                html += f"                <span>Target: <code>{record.element_target}</code></span>\n"

            html += f"""            </div>
            <img src="{screenshot_name}" alt="Step {i}">
        </div>
"""

        html += """    </div>
</body>
</html>
"""

        if output_path:
            output_path.write_text(html)
            logger.info(f"HTML guide saved to {output_path}")

        return html
