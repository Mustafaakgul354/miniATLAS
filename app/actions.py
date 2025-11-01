"""Action executor for browser interactions."""

import asyncio
from typing import Any, Dict, Optional, Tuple

from playwright.async_api import Page, TimeoutError as PlaywrightTimeout

from .config import config
from .schemas import AgentAction, ActionType
from .utils.logging import get_logger
from .utils.selectors import heal_selector

logger = get_logger(__name__)


class ActionExecutor:
    """Executes browser actions via Playwright."""
    
    def __init__(self):
        self.default_timeout = config.browser.default_timeout_ms
        self.wait_after_action = config.agent.wait_after_action_ms
    
    async def execute(
        self,
        page: Page,
        action: AgentAction
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Execute an action on the page.
        Returns (success, error_message, result_data).
        """
        logger.info(f"Executing action: {action.action}")
        
        try:
            # Route to appropriate handler
            if action.action == ActionType.CLICK:
                return await self._execute_click(page, action)
            
            elif action.action == ActionType.FILL:
                return await self._execute_fill(page, action)
            
            elif action.action == ActionType.GOTO:
                return await self._execute_goto(page, action)
            
            elif action.action == ActionType.PRESS:
                return await self._execute_press(page, action)
            
            elif action.action == ActionType.SELECT:
                return await self._execute_select(page, action)
            
            elif action.action == ActionType.WAIT_FOR_SELECTOR:
                return await self._execute_wait(page, action)
            
            elif action.action == ActionType.ASSERT_URL_INCLUDES:
                return await self._execute_assert_url(page, action)
            
            elif action.action == ActionType.DONE:
                return True, None, {"summary": action.summary}
            
            else:
                return False, f"Unknown action type: {action.action}", None
                
        except Exception as e:
            logger.error(f"Action execution failed: {e}")
            return False, str(e), None
    
    async def _execute_click(
        self,
        page: Page,
        action: AgentAction
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Execute click action."""
        selector = action.selector
        
        try:
            # Wait for element to be clickable
            locator = page.locator(selector)
            await locator.wait_for(state="visible", timeout=self.default_timeout)
            
            # Scroll into view if needed
            await locator.scroll_into_view_if_needed()
            
            # Click
            await locator.click()
            
            # Wait after action
            if self.wait_after_action > 0:
                await asyncio.sleep(self.wait_after_action / 1000)
            
            logger.info(f"Clicked: {selector}")
            return True, None, {"clicked": selector}
            
        except PlaywrightTimeout:
            # Try healing selector
            logger.warning(f"Click timeout for selector: {selector}")
            
            alternatives = heal_selector(selector, "Element not found")
            for alt_selector in alternatives[:3]:  # Try top 3 alternatives
                try:
                    locator = page.locator(alt_selector)
                    await locator.wait_for(state="visible", timeout=2000)
                    await locator.click()
                    
                    logger.info(f"Click succeeded with healed selector: {alt_selector}")
                    return True, None, {"clicked": alt_selector, "healed": True}
                    
                except:
                    continue
            
            return False, f"Element not found or not clickable: {selector}", None
            
        except Exception as e:
            return False, f"Click failed: {str(e)}", None
    
    async def _execute_fill(
        self,
        page: Page,
        action: AgentAction
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Execute fill action."""
        selector = action.selector
        value = action.value
        press_enter = action.press_enter
        
        try:
            # Wait for element
            locator = page.locator(selector)
            await locator.wait_for(state="visible", timeout=self.default_timeout)
            
            # Clear existing content
            await locator.clear()
            
            # Type with delay to appear more human-like
            await locator.type(value, delay=50)
            
            # Press Enter if requested
            if press_enter:
                await locator.press("Enter")
            
            # Wait after action
            if self.wait_after_action > 0:
                await asyncio.sleep(self.wait_after_action / 1000)
            
            logger.info(f"Filled {selector} with value (length={len(value)})")
            return True, None, {"filled": selector, "value_length": len(value)}
            
        except PlaywrightTimeout:
            return False, f"Element not found: {selector}", None
        except Exception as e:
            return False, f"Fill failed: {str(e)}", None
    
    async def _execute_goto(
        self,
        page: Page,
        action: AgentAction
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Execute navigation action."""
        url = action.url
        
        try:
            # Navigate with extended timeout
            response = await page.goto(
                url,
                wait_until="domcontentloaded",
                timeout=config.browser.navigation_timeout_ms
            )
            
            # Check response status
            if response and response.status >= 400:
                logger.warning(f"Navigation returned status {response.status}")
            
            # Wait for page to stabilize
            await page.wait_for_load_state("domcontentloaded")
            
            # Additional wait
            if self.wait_after_action > 0:
                await asyncio.sleep(self.wait_after_action / 1000)
            
            final_url = page.url
            logger.info(f"Navigated to: {final_url}")
            
            return True, None, {
                "navigated_to": final_url,
                "status": response.status if response else None
            }
            
        except PlaywrightTimeout:
            return False, f"Navigation timeout: {url}", None
        except Exception as e:
            return False, f"Navigation failed: {str(e)}", None
    
    async def _execute_press(
        self,
        page: Page,
        action: AgentAction
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Execute key press action."""
        key = action.key
        
        try:
            # Press key
            await page.keyboard.press(key)
            
            # Wait after action
            if self.wait_after_action > 0:
                await asyncio.sleep(self.wait_after_action / 1000)
            
            logger.info(f"Pressed key: {key}")
            return True, None, {"pressed": key}
            
        except Exception as e:
            return False, f"Key press failed: {str(e)}", None
    
    async def _execute_select(
        self,
        page: Page,
        action: AgentAction
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Execute select dropdown action."""
        selector = action.selector
        value = action.value
        
        try:
            # Wait for element
            locator = page.locator(selector)
            await locator.wait_for(state="visible", timeout=self.default_timeout)
            
            # Select by value, label, or index
            if value.isdigit():
                # Try as index first
                await locator.select_option(index=int(value))
            else:
                # Try as value or label
                try:
                    await locator.select_option(value=value)
                except:
                    await locator.select_option(label=value)
            
            # Wait after action
            if self.wait_after_action > 0:
                await asyncio.sleep(self.wait_after_action / 1000)
            
            logger.info(f"Selected {value} in {selector}")
            return True, None, {"selected": value, "selector": selector}
            
        except PlaywrightTimeout:
            return False, f"Select element not found: {selector}", None
        except Exception as e:
            return False, f"Select failed: {str(e)}", None
    
    async def _execute_wait(
        self,
        page: Page,
        action: AgentAction
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Execute wait for element action."""
        selector = action.selector
        timeout = action.timeout_ms
        
        try:
            # Wait for element
            locator = page.locator(selector)
            await locator.wait_for(state="visible", timeout=timeout)
            
            logger.info(f"Element appeared: {selector}")
            return True, None, {"found": selector}
            
        except PlaywrightTimeout:
            return False, f"Element did not appear within {timeout}ms: {selector}", None
        except Exception as e:
            return False, f"Wait failed: {str(e)}", None
    
    async def _execute_assert_url(
        self,
        page: Page,
        action: AgentAction
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Execute URL assertion."""
        expected = action.value
        current_url = page.url
        
        if expected in current_url:
            logger.info(f"URL assertion passed: {expected} in {current_url}")
            return True, None, {"url": current_url, "contains": expected}
        else:
            return False, f"URL does not contain '{expected}'. Current: {current_url}", None
    
    async def wait_for_network_idle(self, page: Page, timeout: int = 5000):
        """Wait for network to become idle."""
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
        except PlaywrightTimeout:
            logger.warning("Network idle timeout - continuing anyway")
    
    async def handle_popup(self, page: Page) -> Optional[Page]:
        """Handle popup windows."""
        try:
            # Wait for popup
            async with page.expect_popup() as popup_info:
                popup = await popup_info.value
                logger.info(f"Popup detected: {popup.url}")
                return popup
        except:
            return None


# Global action executor
action_executor = ActionExecutor()
