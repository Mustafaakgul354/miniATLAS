"""Pydantic schemas for API requests/responses and agent actions."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


# API Request/Response Schemas

class SessionMode(str, Enum):
    """Session storage mode."""
    EPHEMERAL = "ephemeral"
    PERSISTENT = "persistent"


class SessionProfile(BaseModel):
    """User profile data for session."""
    email: Optional[str] = None
    password: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class RunRequest(BaseModel):
    """Request to start an agent session."""
    url: str = Field(..., description="Starting URL for the agent")
    goals: List[str] = Field(..., min_items=1, description="List of goals to achieve")
    profile: Optional[SessionProfile] = None
    session_mode: SessionMode = SessionMode.EPHEMERAL
    proxy: Optional[str] = None
    max_steps: int = Field(default=20, ge=1, le=100)
    
    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL has protocol."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class SessionStatus(str, Enum):
    """Agent session status."""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"
    WAITING_HUMAN = "waiting_human"


class RunResponse(BaseModel):
    """Response after starting an agent session."""
    session_id: str
    status: SessionStatus


class ActionInfo(BaseModel):
    """Information about a performed action."""
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class StatusResponse(BaseModel):
    """Session status response."""
    session_id: str
    state: SessionStatus
    current_url: str
    steps_done: int
    last_action: Optional[ActionInfo] = None
    has_captcha: bool = False
    error: Optional[str] = None


class ContinueRequest(BaseModel):
    """Request to continue a paused session."""
    note: Optional[str] = None


# Agent Action Schemas

class ActionType(str, Enum):
    """Supported action types."""
    CLICK = "click"
    FILL = "fill"
    GOTO = "goto"
    PRESS = "press"
    SELECT = "select"
    WAIT_FOR_SELECTOR = "wait_for_selector"
    ASSERT_URL_INCLUDES = "assert_url_includes"
    DONE = "done"


class BaseAction(BaseModel):
    """Base action model."""
    action: ActionType


class ClickAction(BaseAction):
    """Click action."""
    action: Literal[ActionType.CLICK] = ActionType.CLICK
    selector: str


class FillAction(BaseAction):
    """Fill form field action."""
    action: Literal[ActionType.FILL] = ActionType.FILL
    selector: str
    value: str
    press_enter: bool = False


class GotoAction(BaseAction):
    """Navigate to URL action."""
    action: Literal[ActionType.GOTO] = ActionType.GOTO
    url: str
    
    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Ensure URL has protocol."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class PressAction(BaseAction):
    """Press keyboard key action."""
    action: Literal[ActionType.PRESS] = ActionType.PRESS
    key: str


class SelectAction(BaseAction):
    """Select dropdown option action."""
    action: Literal[ActionType.SELECT] = ActionType.SELECT
    selector: str
    value: str


class WaitForSelectorAction(BaseAction):
    """Wait for element action."""
    action: Literal[ActionType.WAIT_FOR_SELECTOR] = ActionType.WAIT_FOR_SELECTOR
    selector: str
    timeout_ms: int = Field(default=10000, ge=1000, le=60000)


class AssertUrlIncludesAction(BaseAction):
    """Assert URL contains value action."""
    action: Literal[ActionType.ASSERT_URL_INCLUDES] = ActionType.ASSERT_URL_INCLUDES
    value: str


class DoneAction(BaseAction):
    """Complete session action."""
    action: Literal[ActionType.DONE] = ActionType.DONE
    summary: str


# Union type for all actions
AgentAction = Union[
    ClickAction,
    FillAction,
    GotoAction,
    PressAction,
    SelectAction,
    WaitForSelectorAction,
    AssertUrlIncludesAction,
    DoneAction
]


# Agent Internal Schemas

class ObservationState(BaseModel):
    """Current page observation."""
    url: str
    title: str
    content: str  # HTML content
    element_count: int
    has_forms: bool = False
    has_buttons: bool = False
    screenshot: Optional[str] = None  # Base64 encoded
    network_events: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentStep(BaseModel):
    """Single step in agent execution."""
    step_number: int
    observation: ObservationState
    reasoning: str
    action: Optional[AgentAction] = None
    result: Optional[str] = None
    error: Optional[str] = None
    duration_ms: int = 0
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentSession(BaseModel):
    """Full agent session data."""
    session_id: str
    url: str
    goals: List[str]
    profile: Optional[SessionProfile] = None
    status: SessionStatus = SessionStatus.RUNNING
    steps: List[AgentStep] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    @property
    def steps_count(self) -> int:
        """Get number of steps taken."""
        return len(self.steps)
    
    @property
    def is_active(self) -> bool:
        """Check if session is still active."""
        return self.status in (SessionStatus.RUNNING, SessionStatus.WAITING_HUMAN)
