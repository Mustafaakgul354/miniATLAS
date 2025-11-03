"""Tests for agent loop functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agent_loop import AgentLoop
from app.schemas import (
    AgentSession, ObservationState, SessionStatus,
    ClickAction, DoneAction
)


@pytest.fixture
def mock_page():
    """Create mock page."""
    page = AsyncMock()
    page.url = "https://example.com"
    page.title = AsyncMock(return_value="Example Page")
    page.content = AsyncMock(return_value="<html><body>Test content</body></html>")
    page.screenshot = AsyncMock(return_value=b"fake-screenshot")
    page.locator = MagicMock()
    return page


@pytest.fixture
def mock_network_monitor():
    """Create mock network monitor."""
    monitor = MagicMock()
    monitor.get_recent_events = MagicMock(return_value=[])
    monitor.clear_old_events = MagicMock()
    return monitor


@pytest.fixture
def test_session():
    """Create test session."""
    return AgentSession(
        session_id="test-session",
        url="https://example.com",
        goals=["Navigate to login", "Login as test user"],
        status=SessionStatus.RUNNING
    )


@pytest.mark.asyncio
async def test_observe(mock_page, mock_network_monitor):
    """Test observation gathering."""
    agent = AgentLoop()
    
    # Mock element counts
    mock_page.locator.return_value.count = AsyncMock(return_value=5)
    
    observation = await agent._observe(mock_page, mock_network_monitor)
    
    assert observation.url == "https://example.com"
    assert observation.title == "Example Page"
    assert "<html>" in observation.content
    assert observation.screenshot is not None


@pytest.mark.asyncio
async def test_format_observation():
    """Test observation formatting."""
    agent = AgentLoop()
    
    observation = ObservationState(
        url="https://example.com/login",
        title="Login Page",
        content='<form><input name="email"><button>Login</button></form>',
        element_count=2,
        has_forms=True,
        has_buttons=True
    )
    
    formatted = agent._format_observation(observation)
    
    assert "https://example.com/login" in formatted
    assert "Login Page" in formatted
    assert "Forms: Yes" in formatted
    assert "Buttons: Yes" in formatted


@pytest.mark.asyncio
async def test_run_step_with_done_action(test_session, mock_page, mock_network_monitor):
    """Test step execution with done action."""
    agent = AgentLoop()
    
    # Mock LLM to return done action
    with patch('app.agent_loop.captcha_handler.detector.detect') as mock_detect:
        mock_detect.return_value = (False, None, None)
        with patch('app.agent_loop.llm_client.generate_action') as mock_generate:
            mock_generate.return_value = DoneAction(summary="Task completed")
            
            # Mock action executor
            with patch('app.agent_loop.action_executor.execute') as mock_execute:
                mock_execute.return_value = (True, None, {"summary": "Task completed"})
                
                step = await agent._run_step(test_session, mock_page, mock_network_monitor)
                
                assert step is not None
                assert step.action.action == "done"
                assert step.result == "Success"


@pytest.mark.asyncio
async def test_captcha_detection(test_session, mock_page, mock_network_monitor):
    """Test CAPTCHA detection during step."""
    agent = AgentLoop()
    
    # Mock CAPTCHA detection
    with patch('app.agent_loop.captcha_handler.detector.detect') as mock_detect:
        mock_detect.return_value = (True, "recaptcha", {})
        
        # Mock CAPTCHA handler to fail (require human)
        with patch('app.agent_loop.captcha_handler.handle') as mock_handle:
            mock_handle.return_value = (False, "CAPTCHA requires human intervention")
            
            step = await agent._run_step(test_session, mock_page, mock_network_monitor)
            
            assert step is not None
            assert "CAPTCHA" in step.error
            assert "human intervention" in step.error


@pytest.mark.asyncio
async def test_action_validation_failure(test_session, mock_page, mock_network_monitor):
    """Test action validation failure."""
    agent = AgentLoop()
    
    # Mock LLM to return click action
    with patch('app.agent_loop.llm_client.generate_action') as mock_generate:
        mock_generate.return_value = ClickAction(selector="button[text='Delete All']")
        
        # Mock validator to reject action
        with patch('app.agent_loop.action_validator.validate_action') as mock_validate:
            mock_validate.return_value = (False, "Deletion actions require confirmation")
            
            step = await agent._run_step(test_session, mock_page, mock_network_monitor)
            
            assert step is not None
            assert "blocked by security policy" in step.reasoning
            assert step.error == "Deletion actions require confirmation"
