"""Network event monitoring for backend validation."""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from playwright.async_api import Request, Response, Route

from .config import config
from .utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class NetworkEvent:
    """Captured network event."""
    
    timestamp: float
    method: str
    url: str
    status: Optional[int] = None
    response_time_ms: Optional[float] = None
    request_headers: Optional[Dict[str, str]] = None
    response_headers: Optional[Dict[str, str]] = None
    request_body: Optional[str] = None
    response_body: Optional[str] = None
    resource_type: Optional[str] = None
    failure: Optional[str] = None
    
    @property
    def is_xhr_or_fetch(self) -> bool:
        """Check if this is an XHR or Fetch request."""
        return self.resource_type in ("xhr", "fetch")
    
    @property
    def is_success(self) -> bool:
        """Check if request was successful."""
        return self.status is not None and 200 <= self.status < 300
    
    @property
    def is_api_call(self) -> bool:
        """Check if this looks like an API call."""
        # Simple heuristics
        return (
            self.is_xhr_or_fetch or
            "/api/" in self.url or
            "/v1/" in self.url or
            "/v2/" in self.url or
            self.url.endswith(".json")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        return {
            "timestamp": self.timestamp,
            "method": self.method,
            "url": self.url,
            "status": self.status,
            "response_time_ms": self.response_time_ms,
            "resource_type": self.resource_type,
            "is_success": self.is_success,
            "is_api_call": self.is_api_call,
            "failure": self.failure
        }


class NetworkMonitor:
    """Monitor and capture network events."""
    
    def __init__(self):
        self.events: List[NetworkEvent] = []
        self._request_start_times: Dict[str, float] = {}
        self.enabled = config.network.record_responses
        self.max_payload_bytes = config.network.max_payload_kb * 1024
    
    async def on_request(self, request: Request):
        """Handle request event."""
        if not self.enabled:
            return
        
        try:
            # Track request start time
            request_id = f"{request.method}:{request.url}"
            self._request_start_times[request_id] = time.time()
            
            # Create initial event
            event = NetworkEvent(
                timestamp=time.time(),
                method=request.method,
                url=request.url,
                resource_type=request.resource_type
            )
            
            # Capture headers if needed
            if config.network.verify_backend_success:
                event.request_headers = await request.all_headers()
            
            # Capture body for POST/PUT/PATCH
            if request.method in ("POST", "PUT", "PATCH"):
                try:
                    post_data = request.post_data
                    if post_data and len(post_data) <= self.max_payload_bytes:
                        event.request_body = post_data
                except:
                    pass
            
            self.events.append(event)
            logger.debug(f"Network request: {request.method} {request.url}")
            
        except Exception as e:
            logger.warning(f"Failed to capture request: {e}")
    
    async def on_response(self, response: Response):
        """Handle response event."""
        if not self.enabled:
            return
        
        try:
            request = response.request
            request_id = f"{request.method}:{request.url}"
            
            # Find matching event
            matching_event = None
            for event in reversed(self.events):
                if event.method == request.method and event.url == request.url and event.status is None:
                    matching_event = event
                    break
            
            if matching_event:
                # Update with response data
                matching_event.status = response.status
                
                # Calculate response time
                if request_id in self._request_start_times:
                    start_time = self._request_start_times.pop(request_id)
                    matching_event.response_time_ms = (time.time() - start_time) * 1000
                
                # Capture response headers
                if config.network.verify_backend_success:
                    matching_event.response_headers = await response.all_headers()
                
                # Capture response body for API calls
                if matching_event.is_api_call:
                    try:
                        body = await response.body()
                        if body and len(body) <= self.max_payload_bytes:
                            matching_event.response_body = body.decode('utf-8', errors='ignore')
                    except:
                        pass
                
                logger.debug(
                    f"Network response: {request.method} {request.url} -> {response.status} "
                    f"({matching_event.response_time_ms:.0f}ms)"
                )
            
        except Exception as e:
            logger.warning(f"Failed to capture response: {e}")
    
    async def on_request_failed(self, request: Request):
        """Handle failed request."""
        if not self.enabled:
            return
        
        try:
            # Find matching event
            for event in reversed(self.events):
                if event.method == request.method and event.url == request.url and event.status is None:
                    event.failure = request.failure
                    logger.warning(f"Network request failed: {request.method} {request.url} - {request.failure}")
                    break
                    
        except Exception as e:
            logger.warning(f"Failed to capture request failure: {e}")
    
    def get_recent_events(
        self,
        seconds: int = 5,
        api_only: bool = True,
        success_only: bool = False
    ) -> List[NetworkEvent]:
        """Get recent network events."""
        cutoff_time = time.time() - seconds
        
        events = [
            event for event in self.events
            if event.timestamp >= cutoff_time
        ]
        
        if api_only:
            events = [e for e in events if e.is_api_call]
        
        if success_only:
            events = [e for e in events if e.is_success]
        
        return events
    
    def check_backend_success(self, url_pattern: str, method: str = "POST") -> bool:
        """Check if a backend call was successful."""
        if not config.network.verify_backend_success:
            return True  # Assume success if verification disabled
        
        # Look for matching successful requests in recent events
        recent = self.get_recent_events(seconds=10)
        
        for event in recent:
            if (
                event.method == method and
                url_pattern in event.url and
                event.is_success
            ):
                return True
        
        return False
    
    def clear_old_events(self, max_age_seconds: int = 300):
        """Clear events older than specified age."""
        cutoff_time = time.time() - max_age_seconds
        self.events = [e for e in self.events if e.timestamp >= cutoff_time]
        
        # Also clear old request timings
        current_time = time.time()
        self._request_start_times = {
            k: v for k, v in self._request_start_times.items()
            if current_time - v < max_age_seconds
        }
    
    def get_summary(self) -> Dict[str, Any]:
        """Get network activity summary."""
        total_events = len(self.events)
        api_events = [e for e in self.events if e.is_api_call]
        successful_events = [e for e in self.events if e.is_success]
        failed_events = [e for e in self.events if e.failure]
        
        avg_response_time = 0
        if api_events:
            times = [e.response_time_ms for e in api_events if e.response_time_ms]
            if times:
                avg_response_time = sum(times) / len(times)
        
        return {
            "total_requests": total_events,
            "api_requests": len(api_events),
            "successful_requests": len(successful_events),
            "failed_requests": len(failed_events),
            "avg_api_response_time_ms": round(avg_response_time, 2)
        }
