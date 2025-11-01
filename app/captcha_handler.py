"""CAPTCHA detection and handling module."""

import asyncio
import base64
from typing import Dict, List, Optional, Tuple

from playwright.async_api import Page

from .config import config
from .llm_client import llm_client
from .utils.logging import get_logger

logger = get_logger(__name__)


class CaptchaDetector:
    """Detects various types of CAPTCHAs on web pages."""
    
    # Common CAPTCHA indicators
    CAPTCHA_SELECTORS = [
        # reCAPTCHA
        'iframe[src*="recaptcha"]',
        'div.g-recaptcha',
        '#g-recaptcha',
        '[data-sitekey]',
        
        # hCaptcha
        'iframe[src*="hcaptcha"]',
        'div.h-captcha',
        '[data-hcaptcha-sitekey]',
        
        # Cloudflare
        'div.cf-challenge',
        '#cf-challenge-running',
        'div.challenge-form',
        
        # Generic patterns
        'img[alt*="captcha" i]',
        'img[src*="captcha" i]',
        'div[class*="captcha" i]',
        'form[class*="captcha" i]',
        'label[for*="captcha" i]',
        'input[name*="captcha" i]',
        'input[placeholder*="captcha" i]',
        
        # Text patterns
        ':has-text("verify you are human")',
        ':has-text("i am not a robot")',
        ':has-text("complete the captcha")',
        ':has-text("security check")'
    ]
    
    # CAPTCHA text patterns in page content
    CAPTCHA_TEXT_PATTERNS = [
        "verify you are human",
        "i am not a robot",
        "i'm not a robot",
        "complete the captcha",
        "enter the code",
        "security check",
        "verification required",
        "prove you're not a robot",
        "select all images"
    ]
    
    async def detect(self, page: Page) -> Tuple[bool, Optional[str], Optional[Dict[str, any]]]:
        """
        Detect CAPTCHA presence on the page.
        Returns (has_captcha, captcha_type, captcha_info).
        """
        try:
            # Quick check with selectors
            for selector in self.CAPTCHA_SELECTORS:
                try:
                    count = await page.locator(selector).count()
                    if count > 0:
                        captcha_type = self._identify_captcha_type(selector)
                        logger.info(f"CAPTCHA detected: {captcha_type} (selector: {selector})")
                        
                        # Get additional info
                        info = await self._get_captcha_info(page, selector, captcha_type)
                        return True, captcha_type, info
                except:
                    continue
            
            # Check page content for CAPTCHA text
            try:
                content = await page.content()
                content_lower = content.lower()
                
                for pattern in self.CAPTCHA_TEXT_PATTERNS:
                    if pattern in content_lower:
                        logger.info(f"CAPTCHA detected via text pattern: {pattern}")
                        return True, "generic", {"text_pattern": pattern}
            except:
                pass
            
            # Check for Cloudflare challenge specifically
            if await self._check_cloudflare_challenge(page):
                return True, "cloudflare", {"challenge_type": "cloudflare"}
            
            return False, None, None
            
        except Exception as e:
            logger.error(f"Error detecting CAPTCHA: {e}")
            return False, None, None
    
    def _identify_captcha_type(self, selector: str) -> str:
        """Identify CAPTCHA type from selector."""
        selector_lower = selector.lower()
        
        if "recaptcha" in selector_lower or "g-recaptcha" in selector_lower:
            return "recaptcha"
        elif "hcaptcha" in selector_lower or "h-captcha" in selector_lower:
            return "hcaptcha"
        elif "cloudflare" in selector_lower or "cf-challenge" in selector_lower:
            return "cloudflare"
        else:
            return "generic"
    
    async def _get_captcha_info(
        self,
        page: Page,
        selector: str,
        captcha_type: str
    ) -> Dict[str, any]:
        """Get additional information about the CAPTCHA."""
        info = {
            "type": captcha_type,
            "selector": selector
        }
        
        try:
            # Get sitekey for reCAPTCHA/hCaptcha
            if captcha_type in ("recaptcha", "hcaptcha"):
                sitekey_element = page.locator('[data-sitekey], [data-hcaptcha-sitekey]').first
                if await sitekey_element.count() > 0:
                    sitekey = await sitekey_element.get_attribute('data-sitekey') or \
                              await sitekey_element.get_attribute('data-hcaptcha-sitekey')
                    if sitekey:
                        info["sitekey"] = sitekey
            
            # Check if it's an image CAPTCHA
            img_elements = await page.locator(f'{selector} img').all()
            if img_elements:
                info["has_images"] = True
                info["image_count"] = len(img_elements)
            
            # Check for input field
            input_element = page.locator(f'{selector} input[type="text"]').first
            if await input_element.count() > 0:
                info["has_input"] = True
                info["input_selector"] = f'{selector} input[type="text"]'
            
        except Exception as e:
            logger.warning(f"Error getting CAPTCHA info: {e}")
        
        return info
    
    async def _check_cloudflare_challenge(self, page: Page) -> bool:
        """Check specifically for Cloudflare challenge."""
        try:
            # Check page title
            title = await page.title()
            if "just a moment" in title.lower() or "checking your browser" in title.lower():
                return True
            
            # Check for challenge script
            has_challenge = await page.evaluate("""
                () => {
                    return window.location.hostname.includes('challenges.cloudflare.com') ||
                           document.querySelector('script[src*="challenges.cloudflare.com"]') !== null;
                }
            """)
            
            return has_challenge
            
        except:
            return False


class CaptchaHandler:
    """Handles CAPTCHA solving attempts."""
    
    def __init__(self):
        self.detector = CaptchaDetector()
        self.max_attempts = 3
    
    async def handle(
        self,
        page: Page,
        screenshot_base64: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Attempt to handle CAPTCHA autonomously.
        Returns (success, error_message).
        """
        # Detect CAPTCHA
        has_captcha, captcha_type, captcha_info = await self.detector.detect(page)
        
        if not has_captcha:
            return True, None
        
        logger.info(f"Attempting to handle {captcha_type} CAPTCHA")
        
        # Try autonomous solving based on type
        if captcha_type == "recaptcha":
            return await self._handle_recaptcha(page, captcha_info)
        
        elif captcha_type == "hcaptcha":
            return await self._handle_hcaptcha(page, captcha_info)
        
        elif captcha_type == "cloudflare":
            return await self._handle_cloudflare(page)
        
        elif captcha_type == "generic":
            return await self._handle_generic_captcha(page, captcha_info, screenshot_base64)
        
        return False, f"Unknown CAPTCHA type: {captcha_type}"
    
    async def _handle_recaptcha(
        self,
        page: Page,
        info: Dict[str, any]
    ) -> Tuple[bool, Optional[str]]:
        """Handle reCAPTCHA challenges."""
        try:
            # Try to find and click the checkbox
            checkbox_selector = 'div.recaptcha-checkbox-border, iframe[src*="recaptcha"] + div'
            
            # Switch to iframe if needed
            frames = page.frames
            for frame in frames:
                if "recaptcha" in frame.url:
                    try:
                        checkbox = frame.locator(checkbox_selector)
                        if await checkbox.count() > 0:
                            await checkbox.click()
                            logger.info("Clicked reCAPTCHA checkbox")
                            
                            # Wait to see if it passes
                            await asyncio.sleep(2)
                            
                            # Check if we need to solve image challenge
                            challenge_frame = page.frame_locator('iframe[src*="recaptcha/api2/bframe"]')
                            if await challenge_frame.locator('div.rc-imageselect').count() > 0:
                                logger.warning("reCAPTCHA image challenge detected - requires human")
                                return False, "reCAPTCHA image challenge requires human intervention"
                            
                            return True, None
                    except:
                        continue
            
            # Try direct click on main page
            checkbox = page.locator('div.g-recaptcha, #g-recaptcha')
            if await checkbox.count() > 0:
                await checkbox.click()
                await asyncio.sleep(2)
                return True, None
            
            return False, "Could not find reCAPTCHA checkbox"
            
        except Exception as e:
            logger.error(f"reCAPTCHA handling failed: {e}")
            return False, str(e)
    
    async def _handle_hcaptcha(
        self,
        page: Page,
        info: Dict[str, any]
    ) -> Tuple[bool, Optional[str]]:
        """Handle hCaptcha challenges."""
        try:
            # Similar to reCAPTCHA, try to click checkbox
            checkbox_selector = 'div[class*="hcaptcha-box"], iframe[src*="hcaptcha"] + div'
            
            checkbox = page.locator(checkbox_selector)
            if await checkbox.count() > 0:
                await checkbox.click()
                logger.info("Clicked hCaptcha checkbox")
                await asyncio.sleep(2)
                
                # Check if image challenge appears
                if await page.locator('div[class*="challenge-container"]').count() > 0:
                    logger.warning("hCaptcha image challenge detected - requires human")
                    return False, "hCaptcha image challenge requires human intervention"
                
                return True, None
            
            return False, "Could not find hCaptcha checkbox"
            
        except Exception as e:
            logger.error(f"hCaptcha handling failed: {e}")
            return False, str(e)
    
    async def _handle_cloudflare(self, page: Page) -> Tuple[bool, Optional[str]]:
        """Handle Cloudflare challenges."""
        try:
            logger.info("Waiting for Cloudflare challenge to complete...")
            
            # Cloudflare challenges often auto-solve after a delay
            max_wait = 30  # seconds
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < max_wait:
                # Check if we've passed the challenge
                title = await page.title()
                if "just a moment" not in title.lower():
                    # Check if we're still on challenge page
                    is_challenge = await page.evaluate("""
                        () => window.location.hostname.includes('challenges.cloudflare.com')
                    """)
                    
                    if not is_challenge:
                        logger.info("Cloudflare challenge passed")
                        return True, None
                
                await asyncio.sleep(1)
            
            return False, "Cloudflare challenge timeout"
            
        except Exception as e:
            logger.error(f"Cloudflare handling failed: {e}")
            return False, str(e)
    
    async def _handle_generic_captcha(
        self,
        page: Page,
        info: Dict[str, any],
        screenshot_base64: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """Handle generic CAPTCHA using vision model."""
        try:
            # Take screenshot if not provided
            if not screenshot_base64 and config.agent.vision_enabled:
                screenshot_bytes = await page.screenshot()
                screenshot_base64 = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            if screenshot_base64 and config.agent.vision_enabled:
                # Use vision model to analyze CAPTCHA
                prompt = """Look at this image. If you see a CAPTCHA:
1. If it's a simple math problem or text to copy, tell me the answer
2. If it's asking to click something specific, describe what to click
3. If it's an image selection task, describe what needs to be selected

Respond with ONLY the answer or action needed, nothing else."""
                
                response = await llm_client.analyze_with_vision(screenshot_base64, prompt)
                logger.info(f"Vision model CAPTCHA response: {response}")
                
                # If there's an input field, try to fill it
                if info.get("has_input") and response:
                    input_selector = info["input_selector"]
                    await page.fill(input_selector, response)
                    
                    # Look for submit button
                    submit_selectors = [
                        'button[type="submit"]',
                        'input[type="submit"]',
                        'button:has-text("submit")',
                        'button:has-text("verify")',
                        'button:has-text("continue")'
                    ]
                    
                    for selector in submit_selectors:
                        if await page.locator(selector).count() > 0:
                            await page.click(selector)
                            await asyncio.sleep(2)
                            
                            # Check if CAPTCHA is gone
                            still_has_captcha, _, _ = await self.detector.detect(page)
                            if not still_has_captcha:
                                return True, None
                            break
                
                # Try to click based on vision response
                if "click" in response.lower():
                    # Extract what to click from response
                    # This is simplified - real implementation would be more sophisticated
                    return False, "Complex CAPTCHA requires human intervention"
            
            return False, "Generic CAPTCHA requires human intervention"
            
        except Exception as e:
            logger.error(f"Generic CAPTCHA handling failed: {e}")
            return False, str(e)
    
    async def wait_for_human_intervention(
        self,
        page: Page,
        timeout: int = 300
    ) -> bool:
        """Wait for human to solve CAPTCHA."""
        logger.info("Waiting for human CAPTCHA intervention...")
        
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check if CAPTCHA is gone
            has_captcha, _, _ = await self.detector.detect(page)
            
            if not has_captcha:
                logger.info("CAPTCHA resolved by human intervention")
                return True
            
            await asyncio.sleep(2)
        
        logger.warning("Timeout waiting for human CAPTCHA intervention")
        return False


# Global CAPTCHA handler
captcha_handler = CaptchaHandler()
