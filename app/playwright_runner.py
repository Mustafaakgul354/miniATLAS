"""Playwright browser and context management."""

import asyncio
import base64
from pathlib import Path
from typing import Any, Dict, Optional

from playwright.async_api import (
    Browser, BrowserContext, Page, Playwright, async_playwright
)

from .config import config
from .netwatch import NetworkMonitor
from .utils.logging import get_logger

logger = get_logger(__name__)


class PlaywrightRunner:
    """Manages Playwright browser instances and contexts."""
    
    def __init__(self):
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self._contexts: Dict[str, BrowserContext] = {}
        self._network_monitors: Dict[str, NetworkMonitor] = {}
    
    async def initialize(self):
        """Initialize Playwright and browser."""
        if self.playwright:
            return
        
        logger.info("Initializing Playwright...")
        self.playwright = await async_playwright().start()
        
        # Launch browser
        launch_args = {
            "headless": config.is_headless,
            "args": ["--disable-blink-features=AutomationControlled"]
        }
        
        # Add proxy if configured
        if config.settings.proxy_url:
            launch_args["proxy"] = {"server": config.settings.proxy_url}
        
        self.browser = await self.playwright.chromium.launch(**launch_args)
        logger.info(f"Browser launched (headless={config.is_headless})")
    
    async def create_context(
        self,
        session_id: str,
        proxy: Optional[str] = None,
        storage_state: Optional[Dict[str, Any]] = None
    ) -> BrowserContext:
        """Create a new browser context for a session."""
        if not self.browser:
            await self.initialize()
        
        # Context options
        context_options = {
            "viewport": {
                "width": config.browser.viewport.width,
                "height": config.browser.viewport.height
            },
            "locale": config.browser.locale,
            "timezone_id": config.browser.timezone,
            "ignore_https_errors": True,
            "java_script_enabled": True
        }
        
        # Add user agent if specified
        if config.settings.user_agent:
            context_options["user_agent"] = config.settings.user_agent
        
        # Add proxy if specified (overrides global proxy)
        if proxy:
            context_options["proxy"] = {"server": proxy}
        elif config.settings.proxy_url:
            context_options["proxy"] = {"server": config.settings.proxy_url}
        
        # Load storage state if persistent mode
        if storage_state:
            context_options["storage_state"] = storage_state
        elif config.browser.storage_mode == "persistent":
            storage_path = Path(config.browser.persistent_dir) / f"{session_id}.json"
            if storage_path.exists():
                context_options["storage_state"] = str(storage_path)
        
        # Create context
        context = await self.browser.new_context(**context_options)
        
        # Set default timeouts
        context.set_default_timeout(config.browser.default_timeout_ms)
        context.set_default_navigation_timeout(config.browser.navigation_timeout_ms)
        
        # Setup network monitoring
        network_monitor = NetworkMonitor()
        context.on("request", network_monitor.on_request)
        context.on("response", network_monitor.on_response)
        context.on("requestfailed", network_monitor.on_request_failed)
        
        # Store context and monitor
        self._contexts[session_id] = context
        self._network_monitors[session_id] = network_monitor
        
        logger.info(f"Created browser context for session {session_id}")
        
        return context
    
    async def get_context(self, session_id: str) -> Optional[BrowserContext]:
        """Get existing context for session."""
        return self._contexts.get(session_id)
    
    async def get_page(self, session_id: str) -> Optional[Page]:
        """Get the active page for a session."""
        context = await self.get_context(session_id)
        if not context:
            return None
        
        pages = context.pages
        if pages:
            return pages[-1]  # Return most recent page
        
        # Create new page if none exists
        return await context.new_page()
    
    async def get_network_monitor(self, session_id: str) -> Optional[NetworkMonitor]:
        """Get network monitor for session."""
        return self._network_monitors.get(session_id)
    
    async def take_screenshot(
        self,
        session_id: str,
        full_page: bool = False
    ) -> Optional[str]:
        """Take screenshot and return base64 encoded image."""
        page = await self.get_page(session_id)
        if not page:
            return None
        
        try:
            screenshot_bytes = await page.screenshot(full_page=full_page)
            return base64.b64encode(screenshot_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return None
    
    async def save_storage_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Save context storage state (cookies, localStorage)."""
        context = await self.get_context(session_id)
        if not context:
            return None
        
        try:
            state = await context.storage_state()
            
            # Save to file if persistent mode
            if config.browser.storage_mode == "persistent":
                storage_dir = Path(config.browser.persistent_dir)
                storage_dir.mkdir(exist_ok=True)
                storage_path = storage_dir / f"{session_id}.json"
                
                import json
                with open(storage_path, 'w') as f:
                    json.dump(state, f)
                
                logger.info(f"Saved storage state for session {session_id}")
            
            return state
            
        except Exception as e:
            logger.error(f"Failed to save storage state: {e}")
            return None
    
    async def close_context(self, session_id: str):
        """Close and cleanup context for session."""
        # Save storage state if needed
        if config.browser.storage_mode == "persistent":
            await self.save_storage_state(session_id)
        
        # Close context
        context = self._contexts.pop(session_id, None)
        if context:
            try:
                await context.close()
                logger.info(f"Closed context for session {session_id}")
            except Exception as e:
                logger.error(f"Error closing context: {e}")
        
        # Remove network monitor
        self._network_monitors.pop(session_id, None)
    
    async def cleanup(self):
        """Cleanup all resources."""
        # Close all contexts
        for session_id in list(self._contexts.keys()):
            await self.close_context(session_id)
        
        # Close browser
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        # Stop playwright
        if self.playwright:
            await self.playwright.stop()
            self.playwright = None
        
        logger.info("Playwright cleanup completed")
    
    async def handle_dialog(self, page: Page, accept: bool = True, prompt_text: str = ""):
        """Setup dialog handler for a page."""
        async def dialog_handler(dialog):
            logger.info(f"Dialog detected: {dialog.type} - {dialog.message}")
            if dialog.type == "prompt":
                await dialog.accept(prompt_text)
            elif accept:
                await dialog.accept()
            else:
                await dialog.dismiss()
        
        page.on("dialog", dialog_handler)
    
    async def block_resources(self, page: Page, resource_types: list = None):
        """Block certain resource types to speed up loading."""
        if resource_types is None:
            resource_types = ["image", "media", "font"]
        
        async def route_handler(route):
            if route.request.resource_type in resource_types:
                await route.abort()
            else:
                await route.continue_()
        
        await page.route("**/*", route_handler)
    
    async def emulate_human_behavior(self, page: Page):
        """Add human-like behavior to avoid detection."""
        # Random mouse movements
        for _ in range(3):
            x = 100 + (await asyncio.get_event_loop().run_in_executor(None, __import__('random').randint, 0, 500))
            y = 100 + (await asyncio.get_event_loop().run_in_executor(None, __import__('random').randint, 0, 400))
            await page.mouse.move(x, y)
            await asyncio.sleep(0.1)
        
        # Random viewport touch
        await page.evaluate("""
            () => {
                // Add some realistic window properties
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
                
                // Add chrome object
                window.chrome = {
                    runtime: {}
                };
                
                // Realistic plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            }
        """)


# Global instance
playwright_runner = PlaywrightRunner()
