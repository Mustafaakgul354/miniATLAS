"""Agent reasoning loop implementation."""

import asyncio
import base64
import inspect
import time
from typing import Dict, List, Optional

from playwright.async_api import Page

from .actions import action_executor
from .captcha_handler import captcha_handler
from .config import config
from .llm_client import llm_client
from .netwatch import NetworkMonitor
from .schemas import (
    AgentAction, AgentSession, AgentStep, ObservationState,
    SessionStatus, ActionType
)
from .utils.logging import get_logger
from .utils.selectors import get_interactive_elements
from .validators import action_validator

logger = get_logger(__name__)


class AgentLoop:
    """Implements the Plan → Act → Observe → Evaluate reasoning loop."""
    
    def __init__(self):
        self.max_steps = config.agent.max_steps
        self.step_timeout = config.settings.agent_step_timeout
        self.total_timeout = config.settings.agent_total_timeout
    
    async def run(
        self,
        session: AgentSession,
        page: Page,
        network_monitor: NetworkMonitor
    ) -> AgentSession:
        """
        Run the agent reasoning loop for a session.
        Returns updated session with results.
        """
        logger.info(f"Starting agent loop for session {session.session_id}")
        start_time = time.time()
        
        try:
            # Navigate to initial URL
            if session.url:
                logger.info(f"Navigating to initial URL: {session.url}")
                await page.goto(session.url, wait_until="domcontentloaded")
                await asyncio.sleep(1)  # Let page stabilize
            
            # Main reasoning loop
            while (
                session.is_active and
                session.steps_count < self.max_steps and
                (time.time() - start_time) < self.total_timeout
            ):
                step_start = time.time()
                
                try:
                    # Run single step with timeout
                    step = await asyncio.wait_for(
                        self._run_step(session, page, network_monitor),
                        timeout=self.step_timeout
                    )
                    
                    if step:
                        step.duration_ms = int((time.time() - step_start) * 1000)
                        session.steps.append(step)
                        
                        # Check if done
                        if step.action and step.action.action == ActionType.DONE:
                            session.status = SessionStatus.COMPLETED
                            logger.info(f"Session completed: {step.action.summary}")
                            break
                    
                    # Check for errors
                    if step.error:
                        logger.warning(f"Step {step.step_number} error: {step.error}")
                        # Continue unless critical error
                        if "human intervention" in step.error.lower():
                            session.status = SessionStatus.WAITING_HUMAN
                            break
                        else:
                            session.status = SessionStatus.FAILED
                            break
                    
                    # Periodic cleanup
                    if session.steps_count % 10 == 0:
                        network_monitor.clear_old_events()
                
                except asyncio.TimeoutError:
                    logger.error(f"Step timeout after {self.step_timeout}s")
                    session.status = SessionStatus.FAILED
                    break
                
                except Exception as e:
                    logger.error(f"Step execution error: {e}")
                    session.status = SessionStatus.FAILED
                    break
            
            # Check termination reason
            if session.is_active:
                if session.steps_count >= self.max_steps:
                    logger.warning(f"Max steps ({self.max_steps}) reached")
                    session.status = SessionStatus.FAILED
                elif (time.time() - start_time) >= self.total_timeout:
                    logger.warning(f"Total timeout ({self.total_timeout}s) reached")
                    session.status = SessionStatus.FAILED
            
            # Set completion time
            from datetime import datetime
            session.completed_at = datetime.utcnow()
            
            logger.info(
                f"Agent loop finished: status={session.status}, "
                f"steps={session.steps_count}, duration={time.time() - start_time:.1f}s"
            )
            
            return session
            
        except Exception as e:
            logger.error(f"Fatal error in agent loop: {e}")
            session.status = SessionStatus.FAILED
            return session
    
    async def _run_step(
        self,
        session: AgentSession,
        page: Page,
        network_monitor: NetworkMonitor
    ) -> Optional[AgentStep]:
        """Execute a single step of the reasoning loop."""
        step_num = session.steps_count + 1
        logger.info(f"Step {step_num}: Observing page state")
        
        # 1. OBSERVE - Gather current state
        observation = await self._observe(page, network_monitor)
        
        # Check for CAPTCHA
        has_captcha, captcha_type, _ = await captcha_handler.detector.detect(page)
        if has_captcha:
            logger.warning(f"CAPTCHA detected: {captcha_type}")
            
            # Try autonomous handling
            if config.agent.vision_enabled:
                screenshot_base64 = observation.screenshot
                success, error = await captcha_handler.handle(page, screenshot_base64)
                
                if success:
                    logger.info("CAPTCHA handled autonomously")
                    # Re-observe after CAPTCHA
                    observation = await self._observe(page, network_monitor)
                else:
                    # Need human intervention
                    return AgentStep(
                        step_number=step_num,
                        observation=observation,
                        reasoning="CAPTCHA detected that requires human intervention",
                        error=error or "CAPTCHA requires human intervention"
                    )
        
        # 2. REASON - Generate next action
        logger.info(f"Step {step_num}: Reasoning about next action")
        
        # Create step history for context
        step_history = [
            {
                "step": s.step_number,
                "action": s.action.model_dump() if s.action else None,
                "result": s.result,
                "error": s.error
            }
            for s in session.steps[-5:]  # Last 5 steps
        ]
        
        # Generate action
        try:
            action = await llm_client.generate_action(
                self._format_observation(observation),
                session.goals,
                step_history
            )
        except Exception as exc:
            logger.error(f"Step {step_num}: LLM provider error: {exc}")
            return AgentStep(
                step_number=step_num,
                observation=observation,
                reasoning="Failed to generate action from LLM provider",
                error=str(exc)
            )
        
        if not action:
            return AgentStep(
                step_number=step_num,
                observation=observation,
                reasoning="Failed to generate valid action",
                error="LLM failed to generate valid action JSON"
            )
        
        # 3. VALIDATE - Check action safety
        logger.info(f"Step {step_num}: Validating action: {action.action}")
        
        is_valid, validation_error = action_validator.validate_action(action, page.url)
        if not is_valid:
            return AgentStep(
                step_number=step_num,
                observation=observation,
                reasoning=f"Action blocked by security policy: {validation_error}",
                action=action,
                error=validation_error
            )
        
        # Check if human confirmation needed
        if action_validator.requires_human_confirmation(action):
            logger.warning(f"Action requires human confirmation: {action}")
            return AgentStep(
                step_number=step_num,
                observation=observation,
                reasoning="Action requires human confirmation",
                action=action,
                error="Sensitive action requires human confirmation"
            )
        
        # 4. ACT - Execute the action
        logger.info(f"Step {step_num}: Executing action")
        
        success, error, result_data = await action_executor.execute(page, action)
        
        # 5. EVALUATE - Check results
        result_summary = "Success" if success else f"Failed: {error}"
        
        # Additional validation for certain actions
        if success and action.action == ActionType.FILL:
            # Verify form submission if needed
            if network_monitor and config.network.verify_backend_success:
                # Wait a bit for potential form submission
                await asyncio.sleep(0.5)
                
                # Check for form submission
                recent_posts = [
                    e for e in network_monitor.get_recent_events(seconds=2)
                    if e.method == "POST"
                ]
                if recent_posts:
                    result_summary += f" (Form submitted to {recent_posts[0].url})"
        
        return AgentStep(
            step_number=step_num,
            observation=observation,
            reasoning=f"Executing {action.action} to progress towards goals",
            action=action,
            result=result_summary,
            error=error
        )
    
    async def _observe(
        self,
        page: Page,
        network_monitor: NetworkMonitor
    ) -> ObservationState:
        """Gather current page state."""
        try:
            # Basic page info
            url = page.url
            title = await page.title()
            
            # Get page content (truncated for efficiency)
            content = await page.content()
            if len(content) > 50000:  # Truncate very large pages
                content = content[:50000] + "\n... [content truncated] ..."
            
            # Count interactive elements
            buttons = await self._count_locator(page, 'button, input[type="button"], input[type="submit"]')
            forms = await self._count_locator(page, 'form')
            inputs = await self._count_locator(page, 'input, textarea, select')
            
            # Take screenshot if enabled
            screenshot_base64 = None
            if config.agent.screenshot_every_step:
                try:
                    screenshot_bytes = await page.screenshot()
                    screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
                except Exception as e:
                    logger.warning(f"Screenshot failed: {e}")
            
            # Get recent network events
            network_events = []
            if network_monitor:
                recent_events = network_monitor.get_recent_events(seconds=5, api_only=True)
                network_events = [e.to_dict() for e in recent_events]
            
            return ObservationState(
                url=url,
                title=title,
                content=content,
                element_count=buttons + inputs,
                has_forms=forms > 0,
                has_buttons=buttons > 0,
                screenshot=screenshot_base64,
                network_events=network_events
            )
            
        except Exception as e:
            logger.error(f"Observation failed: {e}")
            # Return minimal observation
            return ObservationState(
                url=page.url if page else "unknown",
                title="Error",
                content=f"Failed to observe page: {str(e)}",
                element_count=0
            )

    async def _count_locator(self, page: Page, selector: str) -> int:
        """Safely count elements for a selector, handling sync/async mocks."""
        try:
            locator = page.locator(selector)
            if inspect.isawaitable(locator):
                locator = await locator
            
            if not hasattr(locator, "count"):
                return 0
            
            count_result = locator.count()
            if inspect.isawaitable(count_result):
                count_result = await count_result
            
            if isinstance(count_result, bool):
                return int(count_result)
            if isinstance(count_result, (int, float)):
                return int(count_result)
            
            try:
                return int(count_result)
            except (TypeError, ValueError):
                return 0
        
        except Exception as e:
            logger.debug(f"Locator count failed for '{selector}': {e}")
            return 0
    
    def _format_observation(self, observation: ObservationState) -> str:
        """Format observation for LLM consumption."""
        # Get key interactive elements from content
        interactive_summary = self._extract_interactive_elements(observation.content)
        
        formatted = f"""Page URL: {observation.url}
Page Title: {observation.title}

Interactive Elements Summary:
- Forms: {'Yes' if observation.has_forms else 'No'}
- Buttons: {'Yes' if observation.has_buttons else 'No'}
- Total interactive elements: {observation.element_count}

Key Elements Found:
{interactive_summary}

Recent Network Activity:
"""
        
        if observation.network_events:
            for event in observation.network_events[-3:]:  # Last 3 events
                formatted += f"- {event['method']} {event['url']} -> {event.get('status', 'pending')}\n"
        else:
            formatted += "- No recent API calls\n"
        
        # Add truncated content preview
        content_preview = observation.content[:2000] if len(observation.content) > 2000 else observation.content
        formatted += f"\nPage Content Preview:\n{content_preview}"
        
        if len(observation.content) > 2000:
            formatted += "\n... [content truncated] ..."
        
        return formatted
    
    def _extract_interactive_elements(self, html_content: str) -> str:
        """Extract key interactive elements from HTML."""
        # This is a simplified extraction - a real implementation would use
        # proper HTML parsing
        elements = []
        
        # Extract buttons
        import re
        button_matches = re.findall(
            r'<button[^>]*>([^<]+)</button>',
            html_content,
            re.IGNORECASE
        )
        if button_matches:
            elements.append("Buttons: " + ", ".join(set(button_matches[:5])))
        
        # Extract input fields
        input_matches = re.findall(
            r'<input[^>]*(?:name|id|placeholder)=["\']([^"\']+)["\'][^>]*>',
            html_content,
            re.IGNORECASE
        )
        if input_matches:
            elements.append("Input fields: " + ", ".join(set(input_matches[:5])))
        
        # Extract links
        link_matches = re.findall(
            r'<a[^>]*href=["\'][^"\']+["\'][^>]*>([^<]+)</a>',
            html_content,
            re.IGNORECASE
        )
        if link_matches:
            elements.append("Links: " + ", ".join(set(link_matches[:5])))
        
        return "\n".join(elements) if elements else "No interactive elements found"


# Global agent loop instance
agent_loop = AgentLoop()
