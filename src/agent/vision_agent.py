"""Vision-based web agent using multimodal LLMs."""
import json
import base64
from typing import Optional, Literal
from pathlib import Path
from loguru import logger

from anthropic import Anthropic
from openai import OpenAI

from src.agent.schemas import AgentAction, AgentResponse, PageState
from src.agent.prompts import SYSTEM_PROMPT, build_task_prompt, PROJECT_OBJECTIVE


class VisionWebAgent:
    """Agent that uses vision LLM to understand UI and decide actions."""

    def __init__(
        self,
        provider: Literal["claude", "openai"] = "claude",
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[dict] = None,
        project_objective: Optional[str] = None
    ):
        """
        Initialize vision web agent.

        Args:
            provider: LLM provider ("claude" or "openai")
            model: Model name (defaults based on provider)
            api_key: API key for the provider
            config: Additional configuration
            project_objective: High-level mission statement to keep in context
        """
        self.provider = provider
        self.config = config or {}
        self.project_objective = project_objective or PROJECT_OBJECTIVE

        # Set default models
        if model is None:
            model = "claude-sonnet-4-20250514" if provider == "claude" else "gpt-4o"

        self.model = model

        # Initialize client
        if provider == "claude":
            self.client = Anthropic(api_key=api_key)
        elif provider == "openai":
            self.client = OpenAI(api_key=api_key)
        else:
            raise ValueError(f"Unknown provider: {provider}")

        self.action_history = []
        logger.info(f"VisionWebAgent initialized with {provider}/{model}")

    def decide_next_action(
        self,
        goal: str,
        current_state: PageState,
        screenshot_path: str
    ) -> AgentResponse:
        """
        Decide the next action based on current page state.

        Args:
            goal: The task goal to accomplish
            current_state: Current page state with element info
            screenshot_path: Path to screenshot with SoM markers

        Returns:
            AgentResponse with the next action to take
        """
        logger.info("Deciding next action...")

        # Build the task prompt
        elements_dict = [
            {
                "marker_id": el.marker_id,
                "tag_name": el.tag_name,
                "text": el.text,
                "aria_label": el.aria_label,
                "placeholder": el.placeholder,
                "role": el.role
            }
            for el in current_state.elements
        ]

        task_prompt = build_task_prompt(
            goal=goal,
            current_url=current_state.url,
            elements=elements_dict,
            action_history=self.action_history,
            project_objective=self.project_objective
        )

        # Read and encode screenshot
        with open(screenshot_path, "rb") as f:
            screenshot_data = base64.b64encode(f.read()).decode("utf-8")

        # Call LLM
        try:
            if self.provider == "claude":
                response = self._call_claude(task_prompt, screenshot_data)
            else:
                response = self._call_openai(task_prompt, screenshot_data)

            # Parse response
            action = self._parse_action_response(response)

            # Add to history
            self.action_history.append({
                "action_type": action.action_type,
                "target": action.target,
                "step_description": action.step_description
            })

            return AgentResponse(
                action=action,
                confidence=0.85,
                is_task_complete=(action.action_type == "done")
            )

        except Exception as e:
            logger.error(f"Failed to decide action: {e}")
            return AgentResponse(
                action=AgentAction(
                    reasoning=f"Error: {str(e)}",
                    action_type="wait",
                    should_capture_screenshot=False,
                    step_description="Waiting due to error"
                ),
                confidence=0.0,
                error=str(e)
            )

    def _call_claude(self, prompt: str, screenshot_b64: str) -> str:
        """Call Claude API with vision."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.config.get("max_tokens", 4096),
            temperature=self.config.get("temperature", 0.7),
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": screenshot_b64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        return response.content[0].text

    def _call_openai(self, prompt: str, screenshot_b64: str) -> str:
        """Call OpenAI API with vision."""
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=self.config.get("max_tokens", 4096),
            temperature=self.config.get("temperature", 0.7),
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{screenshot_b64}"
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )

        return response.choices[0].message.content

    def _parse_action_response(self, response: str) -> AgentAction:
        """
        Parse LLM response into AgentAction.

        Args:
            response: Raw LLM response text

        Returns:
            AgentAction object
        """
        # Try to extract JSON from response
        try:
            # Find JSON block
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")

            json_str = response[start_idx:end_idx]
            action_dict = json.loads(json_str)

            # Validate and create AgentAction
            return AgentAction(**action_dict)

        except Exception as e:
            logger.error(f"Failed to parse action response: {e}")
            logger.debug(f"Response was: {response}")

            # Return a fallback wait action
            return AgentAction(
                reasoning="Failed to parse LLM response",
                action_type="wait",
                should_capture_screenshot=False,
                step_description="Waiting due to parse error"
            )

    def reset_history(self):
        """Clear action history."""
        self.action_history = []
        logger.debug("Action history cleared")
