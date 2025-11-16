"""Vision-based login agent - uses screenshots to handle authentication."""
import json
import base64
from pathlib import Path
from typing import Optional, Dict, Literal
from loguru import logger

from anthropic import Anthropic
from openai import OpenAI

from src.agent.schemas import AgentAction


class VisionLoginAgent:
    """
    Vision-based login agent that uses screenshots to determine login actions.

    This is simpler and more robust than DOM-based detection because:
    - Works across any web app without brittle selectors
    - Can see the actual UI state including modals, overlays
    - Can handle multi-step login flows naturally
    """

    def __init__(
        self,
        provider: Literal["claude", "openai"] = "claude",
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        """
        Initialize vision login agent.

        Args:
            provider: LLM provider (claude or openai)
            model: Model name
            api_key: API key
        """
        self.provider = provider

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

        logger.info(f"VisionLoginAgent initialized with {provider}/{model}")

    def decide_login_action(
        self,
        screenshot_path: str,
        credentials: Dict[str, str],
        elements: list,
        current_url: str
    ) -> Dict:
        """
        Decide the next login action based on screenshot.

        Args:
            screenshot_path: Path to current screenshot
            credentials: Dict with 'email' and 'password'
            elements: List of ElementInfo objects from SoM
            current_url: Current page URL

        Returns:
            Dict with:
                - action: AgentAction object
                - is_logged_in: bool (True if login is complete)
                - is_login_page: bool (True if on login page)
        """
        logger.debug(f"Deciding login action from screenshot: {screenshot_path}")

        # Read and encode screenshot
        with open(screenshot_path, "rb") as f:
            screenshot_data = base64.b64encode(f.read()).decode()

        # Build element list for context
        element_summary = self._build_element_summary(elements)

        # Create prompt for login
        email = credentials.get('email') or credentials.get('username')

        system_prompt = """You are a login automation agent. Your ONLY job is to help log into web applications.

You will be given:
1. A screenshot of the current page
2. A list of interactive elements with marker IDs
3. User credentials (email and password)

Your task:
- Determine if the page requires login
- If login is needed, provide the EXACT next action to authenticate
- Use the provided credentials EXACTLY as given
- Navigate through multi-step login flows

CRITICAL RULES:
- ONLY use the provided email and password
- NEVER make up fake credentials
- Look for email/username fields, password fields, and login buttons

🚨 EXTREMELY IMPORTANT - LOGIN VS SIGNUP:
- We are logging into an EXISTING account, NOT creating a new account
- ALWAYS click "Sign in" or "Log in" buttons
- NEVER EVER click "Sign up", "Register", "Create account" buttons
- If you see both "Sign in" and "Sign up", ALWAYS choose "Sign in"
- We already have an account - we just need to sign in to it
- Clicking "Sign up" is WRONG and will fail"""

        user_prompt = f"""Current URL: {current_url}

Credentials to use:
- Email: {email}
- Password: [provided]

Interactive elements on page:
{element_summary}

Analyze the screenshot and determine:
1. Is this a login page?
   - TRUE if: Has email/password fields AND "Sign in"/"Log in" button
   - FALSE if: Landing page with "Sign up" or "Get started" (NOT a login page!)
   - Landing pages often have an email field for SIGNUP, not login - don't confuse them!
2. Is the user already logged in? (Look for user avatar, logged-in UI, workspace/dashboard)
3. What is the NEXT action needed?

🚨 CRITICAL: Landing pages vs Login pages:
- Landing page: Has "Sign up", "Get started", "Start free trial" → is_login_page = FALSE
- Login page: Has "Sign in", "Log in", password field → is_login_page = TRUE
- If you see BOTH on the page, it's probably a landing page - click "Sign in" to go to the real login page!

Respond in this EXACT JSON format:
{{
    "is_login_page": true/false,
    "is_logged_in": true/false,
    "reasoning": "Brief explanation of what you see",
    "action": {{
        "action_type": "click" | "type" | "wait" | "done",
        "target": "marker_id or element description",
        "value": "text to type (only for type action)",
        "reasoning": "Why this action",
        "step_description": "User-friendly description"
    }}
}}

Rules:
- 🚨 NEVER CLICK "SIGN UP" - We have an existing account, only click "Sign in" or "Log in"
- If already logged in: action_type = "done"
- If need to click login button: action_type = "click", target = marker_id (for "Sign in" NOT "Sign up")
- If need to type email: action_type = "type", target = marker_id, value = "{email}"
- CRITICAL: After typing email, ALWAYS click "Continue" button BEFORE typing password
- If you see a Continue button after email is filled: action_type = "click", target = continue_button_marker
- IMPORTANT: Even if password field shows dots (autofilled), you MUST type the password
- Password fields may have cached/autofilled passwords - ALWAYS type the correct password anyway
- If need to type password: action_type = "type", value = "[password]"
- Use EXACT email provided: {email}

IMPORTANT LOGIN FLOW:
1. Click "Sign in" (NOT "Sign up") → 2. Type email → 3. Click Continue → 4. ALWAYS type password (even if dots visible) → 5. Click Continue/Login

CRITICAL REMINDERS:
- Never skip typing the password just because you see dots in the password field!
- NEVER click "Sign up" or "Register" - we already have an account!"""

        # Get decision from LLM
        if self.provider == "claude":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": screenshot_data
                                }
                            },
                            {
                                "type": "text",
                                "text": user_prompt
                            }
                        ]
                    }
                ]
            )
            response_text = response.content[0].text
        else:  # openai
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{screenshot_data}"
                                }
                            },
                            {
                                "type": "text",
                                "text": user_prompt
                            }
                        ]
                    }
                ],
                max_tokens=2000
            )
            response_text = response.choices[0].message.content

        # Parse response - extract JSON from markdown code blocks if present
        try:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                # Extract content between ```json and ```
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                # Extract content between ``` and ```
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            else:
                # No code blocks - try to find JSON object in text
                # Look for the first { and last } to extract JSON
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    response_text = response_text[json_start:json_end].strip()

            decision = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse login decision: {e}")
            logger.error(f"Response text: {response_text}")
            # Return safe default
            return {
                "action": AgentAction(
                    action_type="wait",
                    reasoning="Failed to parse login decision",
                    step_description="Waiting to analyze page",
                    should_capture_screenshot=True
                ),
                "is_logged_in": False,
                "is_login_page": False
            }

        # Extract action
        action_data = decision.get("action", {})

        # Replace password placeholders with actual password
        # Claude sometimes uses [provided] instead of [password]
        value = action_data.get("value")
        if value in ["[password]", "[provided]"]:
            action_data["value"] = credentials.get("password")

        # Fix target format - add brackets if it's a plain number
        target = action_data.get("target")
        if target and target.isdigit():
            target = f"[{target}]"

        action = AgentAction(
            action_type=action_data.get("action_type", "wait"),
            target=target,
            value=action_data.get("value"),
            reasoning=action_data.get("reasoning", ""),
            step_description=action_data.get("step_description", ""),
            should_capture_screenshot=True
        )

        result = {
            "action": action,
            "is_logged_in": decision.get("is_logged_in", False),
            "is_login_page": decision.get("is_login_page", False),
            "reasoning": decision.get("reasoning", "")
        }

        logger.info(f"Login decision: {result['reasoning']}")
        logger.info(f"Is logged in: {result['is_logged_in']}")
        logger.info(f"Next action: {action.action_type}")

        return result

    def _build_element_summary(self, elements: list, max_elements: int = 30) -> str:
        """Build a concise summary of interactive elements."""
        if not elements:
            return "No interactive elements marked"

        summary_lines = []
        for i, elem in enumerate(elements[:max_elements]):
            parts = [f"[{elem.marker_id}]"]

            if elem.tag_name:
                parts.append(elem.tag_name)
            if elem.text:
                parts.append(f'"{elem.text[:50]}"')
            if elem.placeholder:
                parts.append(f'placeholder="{elem.placeholder}"')
            if elem.type:
                parts.append(f'type={elem.type}')

            summary_lines.append(" ".join(parts))

        if len(elements) > max_elements:
            summary_lines.append(f"... and {len(elements) - max_elements} more elements")

        return "\n".join(summary_lines)
