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
        
        # Launch browser with stealth args
        launch_args = {
            "headless": config.is_headless,
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-site-isolation-trials"
            ]
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
        
        # Context options with realistic defaults
        context_options = {
            "viewport": {
                "width": config.browser.viewport.width,
                "height": config.browser.viewport.height
            },
            "locale": config.browser.locale,
            "timezone_id": config.browser.timezone,
            "ignore_https_errors": True,
            "java_script_enabled": True,
            # Realistic user agent (Chrome on macOS)
            "user_agent": config.settings.user_agent or (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            # Additional realistic settings (only supported ones)
            "color_scheme": "light"
        }
        
        # Override user agent if explicitly specified
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
        
        # Add comprehensive stealth scripts to avoid detection
        await context.add_init_script("""
            (function() {
                'use strict';
                
                // ===== NAVIGATOR PROPERTIES =====
                
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                    configurable: true
                });
                
                // Override plugins with realistic data
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        const plugins = [
                            {
                                0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format"},
                                description: "Portable Document Format",
                                filename: "internal-pdf-viewer",
                                length: 1,
                                name: "Chrome PDF Plugin"
                            },
                            {
                                0: {type: "application/pdf", suffixes: "pdf", description: ""},
                                description: "",
                                filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                                length: 1,
                                name: "Chrome PDF Viewer"
                            },
                            {
                                0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable"},
                                1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable"},
                                description: "",
                                filename: "internal-nacl-plugin",
                                length: 2,
                                name: "Native Client"
                            }
                        ];
                        plugins.item = function(index) { return this[index] || null; };
                        plugins.namedItem = function(name) {
                            for (let i = 0; i < this.length; i++) {
                                if (this[i].name === name) return this[i];
                            }
                            return null;
                        };
                        return plugins;
                    },
                    configurable: true
                });
                
                // Override mimeTypes
                Object.defineProperty(navigator, 'mimeTypes', {
                    get: () => {
                        const mimeTypes = [
                            {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: navigator.plugins[0]},
                            {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: navigator.plugins[0]},
                            {type: "application/x-nacl", suffixes: "", description: "Native Client Executable", enabledPlugin: navigator.plugins[2]},
                            {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable", enabledPlugin: navigator.plugins[2]}
                        ];
                        mimeTypes.item = function(index) { return this[index] || null; };
                        mimeTypes.namedItem = function(name) {
                            for (let i = 0; i < this.length; i++) {
                                if (this[i].type === name) return this[i];
                            }
                            return null;
                        };
                        return mimeTypes;
                    },
                    configurable: true
                });
                
                // Override languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['tr-TR', 'tr', 'en-US', 'en'],
                    configurable: true
                });
                
                Object.defineProperty(navigator, 'language', {
                    get: () => 'tr-TR',
                    configurable: true
                });
                
                // Hardware concurrency (CPU cores)
                Object.defineProperty(navigator, 'hardwareConcurrency', {
                    get: () => 8,
                    configurable: true
                });
                
                // Device memory
                Object.defineProperty(navigator, 'deviceMemory', {
                    get: () => 8,
                    configurable: true
                });
                
                // Platform
                Object.defineProperty(navigator, 'platform', {
                    get: () => 'MacIntel',
                    configurable: true
                });
                
                // ===== CHROME OBJECT =====
                
                if (!window.chrome) {
                    window.chrome = {};
                }
                
                window.chrome.runtime = {
                    onConnect: undefined,
                    onMessage: undefined
                };
                
                // ===== PERMISSIONS API =====
                
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => {
                    const permissionName = parameters.name;
                    if (permissionName === 'notifications') {
                        return Promise.resolve({ state: Notification.permission });
                    }
                    if (permissionName === 'geolocation') {
                        return Promise.resolve({ state: 'prompt' });
                    }
                    if (permissionName === 'persistent-storage') {
                        return Promise.resolve({ state: 'granted' });
                    }
                    return originalQuery ? originalQuery(parameters) : Promise.resolve({ state: 'prompt' });
                };
                
                // ===== BATTERY API =====
                
                if (navigator.getBattery) {
                    const originalGetBattery = navigator.getBattery;
                    navigator.getBattery = function() {
                        return originalGetBattery.call(navigator).then(battery => {
                            Object.defineProperty(battery, 'charging', { get: () => true, configurable: true });
                            Object.defineProperty(battery, 'chargingTime', { get: () => 0, configurable: true });
                            Object.defineProperty(battery, 'dischargingTime', { get: () => Infinity, configurable: true });
                            Object.defineProperty(battery, 'level', { get: () => 0.85, configurable: true });
                            return battery;
                        });
                    };
                }
                
                // ===== CONNECTION API =====
                
                if (navigator.connection || navigator.mozConnection || navigator.webkitConnection) {
                    const connection = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
                    if (connection) {
                        Object.defineProperty(connection, 'effectiveType', { get: () => '4g', configurable: true });
                        Object.defineProperty(connection, 'downlink', { get: () => 10, configurable: true });
                        Object.defineProperty(connection, 'rtt', { get: () => 50, configurable: true });
                        Object.defineProperty(connection, 'saveData', { get: () => false, configurable: true });
                    }
                }
                
                // ===== MEDIA DEVICES =====
                
                if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
                    const originalEnumerateDevices = navigator.mediaDevices.enumerateDevices;
                    navigator.mediaDevices.enumerateDevices = function() {
                        return originalEnumerateDevices.call(navigator.mediaDevices).then(devices => {
                            return devices.map(device => {
                                if (device.kind === 'videoinput' || device.kind === 'audioinput') {
                                    Object.defineProperty(device, 'label', {
                                        get: () => device.kind === 'videoinput' ? 'FaceTime HD Camera' : 'Built-in Microphone',
                                        configurable: true
                                    });
                                }
                                return device;
                            });
                        });
                    };
                }
                
                // ===== CANVAS FINGERPRINTING PROTECTION =====
                
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function(type) {
                    const context = this.getContext('2d');
                    if (context) {
                        const imageData = context.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < imageData.data.length; i += 4) {
                            imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                        }
                        context.putImageData(imageData, 0, 0);
                    }
                    return originalToDataURL.apply(this, arguments);
                };
                
                const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                CanvasRenderingContext2D.prototype.getImageData = function() {
                    const imageData = originalGetImageData.apply(this, arguments);
                    for (let i = 0; i < imageData.data.length; i += 4) {
                        imageData.data[i] += Math.floor(Math.random() * 3) - 1;
                    }
                    return imageData;
                };
                
                // ===== WEBGL FINGERPRINTING PROTECTION =====
                
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter.apply(this, arguments);
                };
                
                const getParameter2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel Iris OpenGL Engine';
                    }
                    return getParameter2.apply(this, arguments);
                };
                
                // ===== AUDIO FINGERPRINTING PROTECTION =====
                
                if (window.AudioContext || window.webkitAudioContext) {
                    const AudioContext = window.AudioContext || window.webkitAudioContext;
                    const originalCreateOscillator = AudioContext.prototype.createOscillator;
                    AudioContext.prototype.createOscillator = function() {
                        const oscillator = originalCreateOscillator.apply(this, arguments);
                        const originalFrequency = oscillator.frequency.value;
                        Object.defineProperty(oscillator.frequency, 'value', {
                            get: () => originalFrequency + Math.random() * 0.0001,
                            set: function(val) { originalFrequency = val; },
                            configurable: true
                        });
                        return oscillator;
                    };
                }
                
                // ===== FONT FINGERPRINTING PROTECTION =====
                
                const originalOffsetWidth = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetWidth').get;
                const originalOffsetHeight = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight').get;
                
                Object.defineProperty(HTMLElement.prototype, 'offsetWidth', {
                    get: function() {
                        const width = originalOffsetWidth.call(this);
                        return width + (Math.random() < 0.5 ? -1 : 1) * Math.random() * 0.1;
                    },
                    configurable: true
                });
                
                Object.defineProperty(HTMLElement.prototype, 'offsetHeight', {
                    get: function() {
                        const height = originalOffsetHeight.call(this);
                        return height + (Math.random() < 0.5 ? -1 : 1) * Math.random() * 0.1;
                    },
                    configurable: true
                });
                
                // ===== SCREEN PROPERTIES =====
                
                Object.defineProperty(screen, 'availWidth', {
                    get: () => 1366,
                    configurable: true
                });
                
                Object.defineProperty(screen, 'availHeight', {
                    get: () => 768,
                    configurable: true
                });
                
                Object.defineProperty(screen, 'width', {
                    get: () => 1366,
                    configurable: true
                });
                
                Object.defineProperty(screen, 'height', {
                    get: () => 768,
                    configurable: true
                });
                
                Object.defineProperty(screen, 'colorDepth', {
                    get: () => 24,
                    configurable: true
                });
                
                Object.defineProperty(screen, 'pixelDepth', {
                    get: () => 24,
                    configurable: true
                });
                
                // ===== CONSOLE DEBUGGER PROTECTION =====
                
                const originalLog = console.log;
                console.log = function() {
                    if (arguments[0] && typeof arguments[0] === 'string' && arguments[0].includes('webdriver')) {
                        return;
                    }
                    return originalLog.apply(console, arguments);
                };
                
                // ===== PLUGIN DETAILS =====
                
                if (navigator.plugins && navigator.plugins.length > 0) {
                    for (let i = 0; i < navigator.plugins.length; i++) {
                        const plugin = navigator.plugins[i];
                        if (plugin && plugin[0]) {
                            Object.defineProperty(plugin[0], 'type', {
                                get: () => plugin[0].type || 'application/x-google-chrome-pdf',
                                configurable: true
                            });
                        }
                    }
                }
                
            })();
        """)
        
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
        
        logger.info(f"Created browser context for session {session_id} (stealth mode enabled)")
        
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
        import random
        
        try:
            # Check if page is still open
            if page.is_closed():
                logger.warning("Page is closed, skipping human behavior")
                return
            
            # Random mouse movements before interaction
            viewport = page.viewport_size
            if viewport and viewport.get('width') and viewport.get('height'):
                for _ in range(random.randint(2, 4)):
                    if page.is_closed():
                        break
                    x = random.randint(50, max(100, viewport['width'] - 50))
                    y = random.randint(50, max(100, viewport['height'] - 50))
                    try:
                        await page.mouse.move(x, y, steps=random.randint(5, 15))
                        await asyncio.sleep(random.uniform(0.05, 0.15))
                    except Exception:
                        break
            
            # Simulate human-like scroll behavior (only if page is still open)
            if not page.is_closed():
                try:
                    await page.evaluate("""
                        () => {
                            // Random small scroll
                            window.scrollBy(0, Math.random() * 50);
                        }
                    """)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                except Exception:
                    pass
            
            # Add realistic mouse trail (only if page is still open)
            if not page.is_closed():
                try:
                    await page.evaluate("""
                        () => {
                            // Simulate mouse presence
                            document.addEventListener('mousemove', function(e) {
                                // Track mouse movement
                            }, { passive: true });
                        }
                    """)
                except Exception:
                    pass
            
        except Exception as e:
            logger.warning(f"Error in human behavior emulation: {e}")


# Global instance
playwright_runner = PlaywrightRunner()
