"""Action executor for browser interactions."""

import asyncio
from typing import Any, Dict, List, Optional, Tuple

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
            
            # Check if multiple elements match (strict mode violation)
            count = await locator.count()
            if count > 1:
                logger.warning(f"Multiple elements ({count}) found for selector: {selector}, using first")
                locator = locator.first
            
            await locator.wait_for(state="visible", timeout=self.default_timeout)
            
            # Scroll into view if needed
            await locator.scroll_into_view_if_needed()
            
            # Human-like click: move mouse to element first, then click
            import random
            box = await locator.bounding_box()
            if box:
                # Move mouse to element with slight randomness
                center_x = box['x'] + box['width'] / 2 + random.uniform(-2, 2)
                center_y = box['y'] + box['height'] / 2 + random.uniform(-2, 2)
                await page.mouse.move(center_x, center_y, steps=random.randint(5, 15))
                await asyncio.sleep(random.uniform(0.05, 0.15))  # Small pause before click
            
            # Click with slight delay
            await locator.click(delay=random.randint(50, 150))
            
            # Wait after action
            if self.wait_after_action > 0:
                await asyncio.sleep(self.wait_after_action / 1000)
            
            logger.info(f"Clicked: {selector}")
            return True, None, {"clicked": selector, "multiple_found": count > 1}
            
        except PlaywrightTimeout:
            # Try healing selector
            logger.warning(f"Click timeout for selector: {selector}")
            
            alternatives = heal_selector(selector, "Element not found")
            for alt_selector in alternatives[:3]:  # Try top 3 alternatives
                try:
                    locator = page.locator(alt_selector)
                    count = await locator.count()
                    if count > 1:
                        locator = locator.first
                    await locator.wait_for(state="visible", timeout=2000)
                    await locator.click()
                    
                    logger.info(f"Click succeeded with healed selector: {alt_selector}")
                    return True, None, {"clicked": alt_selector, "healed": True}
                    
                except:
                    continue
            
            return False, f"Element not found or not clickable: {selector}", None
            
        except Exception as e:
            error_msg = str(e)
            # Handle strict mode violation
            if "strict mode violation" in error_msg.lower() or "resolved to" in error_msg.lower():
                try:
                    logger.warning(f"Strict mode violation for {selector}, trying first match")
                    locator = page.locator(selector).first
                    await locator.wait_for(state="visible", timeout=self.default_timeout)
                    await locator.scroll_into_view_if_needed()
                    await locator.click()
                    
                    if self.wait_after_action > 0:
                        await asyncio.sleep(self.wait_after_action / 1000)
                    
                    logger.info(f"Clicked first match: {selector}")
                    return True, None, {"clicked": selector, "used_first": True}
                except Exception as retry_error:
                    return False, f"Click failed (multiple elements): {str(retry_error)}", None
            
            return False, f"Click failed: {error_msg}", None
    
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
            
            # Type with human-like delays (variable per character)
            import random
            for char in value:
                await locator.type(char, delay=random.randint(30, 120))
                # Occasional longer pauses (like humans do)
                if random.random() < 0.1:  # 10% chance
                    await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Press Enter if requested
            if press_enter:
                await locator.press("Enter")
            
            # Wait after action
            if self.wait_after_action > 0:
                await asyncio.sleep(self.wait_after_action / 1000)
            
            logger.info(f"Filled {selector} with value (length={len(value)})")
            return True, None, {"filled": selector, "value_length": len(value)}
            
        except PlaywrightTimeout:
            # Try alternative selectors for form fields
            logger.warning(f"Fill timeout for selector: {selector}, trying alternatives")
            
            # Generate alternative selectors
            alternatives = self._get_fill_alternatives(selector, value)
            
            for alt_selector in alternatives:
                try:
                    locator = page.locator(alt_selector)
                    count = await locator.count()
                    if count == 0:
                        continue
                    if count > 1:
                        locator = locator.first
                    
                    await locator.wait_for(state="visible", timeout=2000)
                    await locator.clear()
                    await locator.type(value, delay=50)
                    
                    if press_enter:
                        await locator.press("Enter")
                    
                    if self.wait_after_action > 0:
                        await asyncio.sleep(self.wait_after_action / 1000)
                    
                    logger.info(f"Filled with alternative selector: {alt_selector}")
                    return True, None, {"filled": alt_selector, "healed": True, "value_length": len(value)}
                    
                except Exception:
                    continue
            
            return False, f"Element not found: {selector}", None
            
        except Exception as e:
            error_msg = str(e)
            # Try alternatives on any error
            logger.warning(f"Fill error for {selector}: {error_msg}, trying alternatives")
            
            alternatives = self._get_fill_alternatives(selector, value)
            for alt_selector in alternatives:
                try:
                    locator = page.locator(alt_selector)
                    count = await locator.count()
                    if count == 0:
                        continue
                    if count > 1:
                        locator = locator.first
                    
                    await locator.wait_for(state="visible", timeout=2000)
                    await locator.clear()
                    await locator.type(value, delay=50)
                    
                    if press_enter:
                        await locator.press("Enter")
                    
                    if self.wait_after_action > 0:
                        await asyncio.sleep(self.wait_after_action / 1000)
                    
                    logger.info(f"Filled with alternative selector: {alt_selector}")
                    return True, None, {"filled": alt_selector, "healed": True, "value_length": len(value)}
                    
                except Exception:
                    continue
            
            return False, f"Fill failed: {error_msg}", None
    
    def _get_fill_alternatives(self, selector: str, value: str) -> List[str]:
        """Generate alternative selectors for form fields."""
        alternatives = []
        
        # If selector contains name attribute, try variations
        if "name=" in selector:
            # Extract name value
            try:
                name_match = selector.split("name=")[1].split("]")[0].strip("'\"")
                alternatives.extend([
                    f"input[name='{name_match}']",
                    f"input[name=\"{name_match}\"]",
                    f"input[placeholder*='{name_match}']",
                    f"input[aria-label*='{name_match}']",
                    f"input[id*='{name_match}']",
                ])
            except:
                pass
        
        # Try common email/password field patterns
        if "@" in value or "email" in selector.lower() or "e-posta" in selector.lower():
            alternatives.extend([
                "input[type='email']",
                "input[type='text'][placeholder*='email' i]",
                "input[type='text'][placeholder*='e-posta' i]",
                "input[type='text'][placeholder*='mail' i]",
                "input[aria-label*='email' i]",
                "input[aria-label*='e-posta' i]",
                "input[id*='email']",
                "input[id*='mail']",
                "input[name*='email']",
                "input[name*='mail']",
            ])
        
        if "password" in selector.lower() or "şifre" in selector.lower():
            alternatives.extend([
                "input[type='password']",
                "input[placeholder*='password' i]",
                "input[placeholder*='şifre' i]",
                "input[aria-label*='password' i]",
                "input[aria-label*='şifre' i]",
                "input[id*='password']",
                "input[id*='pass']",
                "input[name*='password']",
                "input[name*='pass']",
            ])
        
        # Try generic input selectors
        alternatives.extend([
            "input[type='text']:visible",
            "input:visible",
        ])
        
        # Add healed selector alternatives
        alternatives.extend(heal_selector(selector, "Element not found"))
        
        return alternatives
    
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
