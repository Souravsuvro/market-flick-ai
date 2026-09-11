"""Rate limiting middleware for API protection."""
import time
from typing import Dict, Tuple
from collections import defaultdict
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter implementation."""
    
    def __init__(self, requests_per_minute: int = 60, requests_per_hour: int = 1000):
        """Initialize rate limiter.
        
        Args:
            requests_per_minute: Max requests per minute per user
            requests_per_hour: Max requests per hour per user
        """
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.user_requests: Dict[str, list] = defaultdict(list)
    
    def is_rate_limited(self, user_id: str) -> Tuple[bool, Dict]:
        """Check if user has exceeded rate limits.
        
        Args:
            user_id: Unique user identifier
            
        Returns:
            Tuple of (is_limited: bool, info: dict with remaining requests)
        """
        now = time.time()
        minute_ago = now - 60
        hour_ago = now - 3600
        
        # Clean old requests
        self.user_requests[user_id] = [
            req_time for req_time in self.user_requests[user_id]
            if req_time > hour_ago
        ]
        
        # Count recent requests
        minute_requests = sum(
            1 for req_time in self.user_requests[user_id]
            if req_time > minute_ago
        )
        hour_requests = len(self.user_requests[user_id])
        
        # Check limits
        minute_limit_exceeded = minute_requests >= self.requests_per_minute
        hour_limit_exceeded = hour_requests >= self.requests_per_hour
        
        if minute_limit_exceeded or hour_limit_exceeded:
            logger.warning(
                f"Rate limit exceeded for user {user_id}: "
                f"minute={minute_requests}/{self.requests_per_minute}, "
                f"hour={hour_requests}/{self.requests_per_hour}"
            )
            return True, {
                "minute_remaining": max(0, self.requests_per_minute - minute_requests),
                "hour_remaining": max(0, self.requests_per_hour - hour_requests),
                "reset_minute": int(minute_ago + 60),
                "reset_hour": int(hour_ago + 3600)
            }
        
        # Record request
        self.user_requests[user_id].append(now)
        
        return False, {
            "minute_remaining": self.requests_per_minute - minute_requests - 1,
            "hour_remaining": self.requests_per_hour - hour_requests - 1
        }


# Global rate limiter instance
rate_limiter = RateLimiter(requests_per_minute=60, requests_per_hour=1000)
