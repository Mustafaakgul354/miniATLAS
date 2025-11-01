"""Validation and security guardrails for agent actions."""

import re
from typing import List, Optional, Tuple
from urllib.parse import urlparse

from .config import config
from .schemas import AgentAction, ActionType
from .utils.logging import get_logger

logger = get_logger(__name__)


class ActionValidator:
    """Validates and applies security rules to agent actions."""
    
    # Sensitive action patterns
    PAYMENT_PATTERNS = [
        r"payment",
        r"checkout",
        r"purchase",
        r"buy\s*now",
        r"place\s*order",
        r"confirm\s*order",
        r"submit\s*payment",
        r"pay\s*now"
    ]
    
    DELETION_PATTERNS = [
        r"delete",
        r"remove",
        r"destroy",
        r"erase",
        r"clear\s*all",
        r"permanently"
    ]
    
    FILE_PATTERNS = [
        r"upload",
        r"file",
        r"attachment",
        r"browse",
        r"choose\s*file"
    ]
    
    def __init__(self):
        self.allowed_domains: List[str] = []
        self.blocked_domains: List[str] = []
    
    def validate_action(
        self,
        action: AgentAction,
        current_url: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate an action for safety and security.
        Returns (is_valid, error_message).
        """
        # Check action-specific validation
        if action.action == ActionType.GOTO:
            return self._validate_navigation(action, current_url)
        
        elif action.action == ActionType.CLICK:
            return self._validate_click(action)
        
        elif action.action == ActionType.FILL:
            return self._validate_fill(action)
        
        elif action.action in (ActionType.PRESS, ActionType.SELECT):
            # Generally safe actions
            return True, None
        
        elif action.action == ActionType.WAIT_FOR_SELECTOR:
            # Validate timeout
            if action.timeout_ms > 60000:  # Max 60 seconds
                return False, "Wait timeout exceeds maximum allowed (60s)"
            return True, None
        
        elif action.action == ActionType.ASSERT_URL_INCLUDES:
            # Safe action
            return True, None
        
        elif action.action == ActionType.DONE:
            # Always allowed
            return True, None
        
        return True, None
    
    def _validate_navigation(
        self,
        action: AgentAction,
        current_url: str
    ) -> Tuple[bool, Optional[str]]:
        """Validate navigation action."""
        target_url = action.url
        
        # Parse URLs
        try:
            current_parsed = urlparse(current_url)
            target_parsed = urlparse(target_url)
        except Exception:
            return False, "Invalid URL format"
        
        # Check if navigation is allowed
        if not config.agent.allow_navigation:
            # Only allow same-origin navigation
            if (current_parsed.netloc != target_parsed.netloc):
                return False, "Cross-origin navigation not allowed"
        
        # Check domain allowlist/blocklist
        if self.allowed_domains and target_parsed.netloc not in self.allowed_domains:
            return False, f"Domain {target_parsed.netloc} not in allowed list"
        
        if target_parsed.netloc in self.blocked_domains:
            return False, f"Domain {target_parsed.netloc} is blocked"
        
        # Warn about potential external navigation
        if current_parsed.netloc != target_parsed.netloc:
            logger.warning(f"External navigation: {current_parsed.netloc} -> {target_parsed.netloc}")
        
        return True, None
    
    def _validate_click(self, action: AgentAction) -> Tuple[bool, Optional[str]]:
        """Validate click action."""
        selector = action.selector.lower()
        
        # Check for file dialog triggers
        if config.security.block_file_dialogs:
            for pattern in self.FILE_PATTERNS:
                if re.search(pattern, selector, re.IGNORECASE):
                    return False, "File dialog actions are blocked"
        
        # Check for sensitive actions requiring confirmation
        if config.security.confirm_sensitive_actions:
            # Check payment patterns
            for pattern in self.PAYMENT_PATTERNS:
                if re.search(pattern, selector, re.IGNORECASE):
                    logger.warning(f"Payment action detected: {selector}")
                    return False, "Payment actions require manual confirmation"
            
            # Check deletion patterns
            for pattern in self.DELETION_PATTERNS:
                if re.search(pattern, selector, re.IGNORECASE):
                    logger.warning(f"Deletion action detected: {selector}")
                    return False, "Deletion actions require manual confirmation"
        
        return True, None
    
    def _validate_fill(self, action: AgentAction) -> Tuple[bool, Optional[str]]:
        """Validate fill action."""
        # Check for credit card patterns
        if re.match(r'^\d{13,19}$', action.value):
            logger.warning("Possible credit card number detected in fill action")
            if config.security.confirm_sensitive_actions:
                return False, "Credit card input requires manual confirmation"
        
        # Check for SSN patterns
        if re.match(r'^\d{3}-\d{2}-\d{4}$', action.value):
            logger.warning("Possible SSN detected in fill action")
            if config.security.confirm_sensitive_actions:
                return False, "SSN input requires manual confirmation"
        
        # Redact passwords in logs
        if 'password' in action.selector.lower():
            logger.info(f"Filling password field: {action.selector}")
        
        return True, None
    
    def requires_human_confirmation(self, action: AgentAction) -> bool:
        """Check if action requires human confirmation."""
        if not config.security.confirm_sensitive_actions:
            return False
        
        # Check action type and content
        if action.action == ActionType.CLICK:
            selector_lower = action.selector.lower()
            
            # Check all sensitive patterns
            all_patterns = self.PAYMENT_PATTERNS + self.DELETION_PATTERNS
            for pattern in all_patterns:
                if re.search(pattern, selector_lower, re.IGNORECASE):
                    return True
        
        elif action.action == ActionType.FILL:
            # Check for sensitive data patterns
            if re.match(r'^\d{13,19}$', action.value):  # Credit card
                return True
            if re.match(r'^\d{3}-\d{2}-\d{4}$', action.value):  # SSN
                return True
        
        elif action.action == ActionType.GOTO:
            # External navigation might need confirmation
            # This would need current URL context
            pass
        
        return False
    
    def sanitize_selector(self, selector: str) -> str:
        """Sanitize selector to prevent injection attacks."""
        # Remove potentially dangerous characters
        sanitized = selector.replace('"', '\\"').replace("'", "\\'")
        
        # Limit length
        if len(sanitized) > 500:
            sanitized = sanitized[:500]
        
        return sanitized
    
    def is_safe_url(self, url: str) -> bool:
        """Check if URL is safe to navigate to."""
        try:
            parsed = urlparse(url)
            
            # Only allow http(s)
            if parsed.scheme not in ('http', 'https'):
                return False
            
            # Check for local/internal IPs
            if parsed.hostname in ('localhost', '127.0.0.1', '0.0.0.0'):
                return False
            
            # Check for private IP ranges
            import ipaddress
            try:
                ip = ipaddress.ip_address(parsed.hostname)
                if ip.is_private:
                    return False
            except ValueError:
                # Not an IP address, probably a domain
                pass
            
            return True
            
        except Exception:
            return False


# Global validator instance
action_validator = ActionValidator()
