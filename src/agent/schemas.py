"""Data schemas for agent actions and responses."""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class AgentAction(BaseModel):
    """Structured action output from the vision agent."""

    reasoning: str = Field(description="Explanation of why this action is chosen")
    action_type: Literal["click", "type", "navigate", "wait", "scroll", "done"] = Field(
        description="Type of action to perform"
    )
    target: Optional[str] = Field(
        default=None,
        description="Element marker number [N] or description of target"
    )
    value: Optional[str] = Field(
        default=None,
        description="Text to type or URL to navigate to"
    )
    should_capture_screenshot: bool = Field(
        description="Whether to capture a screenshot after this action"
    )
    step_description: str = Field(
        description="Human-readable description of what this step accomplishes"
    )
    scroll_direction: Optional[Literal["up", "down"]] = Field(
        default=None,
        description="Direction to scroll if action_type is scroll"
    )


class AgentResponse(BaseModel):
    """Complete response from the vision agent."""

    action: AgentAction
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    is_task_complete: bool = Field(default=False)
    error: Optional[str] = Field(default=None)


class ElementInfo(BaseModel):
    """Information about an interactive element on the page."""

    marker_id: int
    tag_name: str
    text: Optional[str] = None
    role: Optional[str] = None
    aria_label: Optional[str] = None
    placeholder: Optional[str] = None
    href: Optional[str] = None
    type: Optional[str] = None


class PageState(BaseModel):
    """Represents the current state of a web page."""

    url: str
    title: str
    screenshot_path: Optional[str] = None
    elements: list[ElementInfo] = Field(default_factory=list)
    dom_hash: Optional[str] = None
    timestamp: float
