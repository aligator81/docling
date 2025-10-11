import time
import hashlib
import threading
from typing import Dict, Tuple, Optional
from fastapi import Request, HTTPException
import logging

logger = logging.getLogger(__name__)

class InMemoryRateLimiter:
    def __init__(self):
        # Rate limit configurations (requests per window)
        self.limits = {
            'upload': {'requests': 10, 'window': 3600},      # 10 uploads per hour
            'chat': {'requests': 60, 'window': 60},         # 60 chats per minute
            'api': {'requests': 1000, 'window': 3600},      # 1000 API calls per hour
            'extract': {'requests': 20, 'window': 3600},    # 20 extractions per hour
            'admin': {'requests': 100, 'window': 3600},     # 100 admin actions per hour
        }

        # In-memory storage for rate limit counters
        # Structure: {client_id: {endpoint_type: {window: count}}}
        self.counters: Dict[str, Dict[str, Dict[int, int]]] = {}
        self._lock = threading.Lock()

    def _get_client_identifier(self, request: Request) -> str:
        """Generate unique client identifier"""
        # Use IP address and User-Agent for identification
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get('user-agent', 'unknown')

        # Create hash of the combination for consistent identification
        identifier = f"{client_ip}:{user_agent}"
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def _get_endpoint_type(self, request: Request) -> str:
        """Determine the type of endpoint being accessed"""
        path = request.url.path

        if path.startswith("/api/documents/upload"):
            return "upload"
        elif path.startswith("/api/chat"):
            return "chat"
        elif path.startswith("/api/documents") and "extract" in path:
            return "extract"
        elif path.startswith("/api/admin"):
            return "admin"
        else:
            return "api"

    def _get_client_identifier(self, request: Request) -> str:
        """Generate unique client identifier"""
        # Use IP address and User-Agent for identification
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get('user-agent', 'unknown')

        # Create hash of the combination for consistent identification
        identifier = f"{client_ip}:{user_agent}"
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def _get_endpoint_type(self, request: Request) -> str:
        """Determine the type of endpoint being accessed"""
        path = request.url.path

        if path.startswith("/api/documents/upload"):
            return "upload"
        elif path.startswith("/api/chat"):
            return "chat"
        elif path.startswith("/api/documents") and "extract" in path:
            return "extract"
        elif path.startswith("/api/admin"):
            return "admin"
        else:
            return "api"

    async def check_rate_limit(self, request: Request) -> bool:
        """Check if request exceeds rate limit"""
        try:
            client_id = self._get_client_identifier(request)
            endpoint_type = self._get_endpoint_type(request)

            # Get rate limit configuration
            limit_config = self.limits.get(endpoint_type, self.limits['api'])

            # Create time window key
            current_window = int(time.time()) // limit_config['window']

            with self._lock:
                # Initialize client data if not exists
                if client_id not in self.counters:
                    self.counters[client_id] = {}

                if endpoint_type not in self.counters[client_id]:
                    self.counters[client_id][endpoint_type] = {}

                # Get current count for this window
                current_count = self.counters[client_id][endpoint_type].get(current_window, 0)

                # Check if limit exceeded
                if current_count >= limit_config['requests']:
                    logger.warning(f"Rate limit exceeded for {client_id} on {endpoint_type}")
                    return False

                # Increment counter
                self.counters[client_id][endpoint_type][current_window] = current_count + 1

            return True

        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            # Fail open - allow request if rate limiting fails
            return True

    def get_remaining_limit(self, request: Request) -> Tuple[int, int]:
        """Get remaining requests and window time for client"""
        try:
            client_id = self._get_client_identifier(request)
            endpoint_type = self._get_endpoint_type(request)
            limit_config = self.limits.get(endpoint_type, self.limits['api'])

            current_window = int(time.time()) // limit_config['window']

            with self._lock:
                # Get current count for this window
                current_count = 0
                if client_id in self.counters and endpoint_type in self.counters[client_id]:
                    current_count = self.counters[client_id][endpoint_type].get(current_window, 0)

                remaining = max(0, limit_config['requests'] - current_count)

                # Calculate remaining window time
                window_start = current_window * limit_config['window']
                remaining_time = (window_start + limit_config['window']) - int(time.time())

                return remaining, max(0, remaining_time)

        except Exception as e:
            logger.error(f"Error getting remaining limit: {str(e)}")
            return 999, 3600

# Global rate limiter instance
rate_limiter = InMemoryRateLimiter()

async def rate_limit_middleware(request: Request, call_next):
    """Middleware function to apply rate limiting"""
    # Check rate limit
    is_allowed = await rate_limiter.check_rate_limit(request)

    if not is_allowed:
        # Get limit details for response headers
        endpoint_type = rate_limiter._get_endpoint_type(request)
        limit_config = rate_limiter.limits.get(endpoint_type, rate_limiter.limits['api'])
        remaining, reset_time = rate_limiter.get_remaining_limit(request)

        # Create response with rate limit headers
        from fastapi.responses import JSONResponse
        response = JSONResponse(
            status_code=429,
            content={
                "error": "Rate limit exceeded",
                "detail": f"Too many requests. Limit: {limit_config['requests']} per {limit_config['window']} seconds",
                "retry_after": reset_time
            }
        )

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit_config['requests'])
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + reset_time)
        response.headers["Retry-After"] = str(reset_time)

        return response

    # Process request normally
    response = await call_next(request)

    # Add rate limit headers to successful responses
    endpoint_type = rate_limiter._get_endpoint_type(request)
    limit_config = rate_limiter.limits.get(endpoint_type, rate_limiter.limits['api'])
    remaining, reset_time = rate_limiter.get_remaining_limit(request)

    response.headers["X-RateLimit-Limit"] = str(limit_config['requests'])
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    response.headers["X-RateLimit-Reset"] = str(int(time.time()) + reset_time)

    return response

# Dependency for FastAPI routes that need rate limiting
def check_rate_limit_dependency(request: Request):
    """Dependency that can be used in FastAPI routes for rate limiting"""
    is_allowed = rate_limiter.check_rate_limit(request)

    if not is_allowed:
        endpoint_type = rate_limiter._get_endpoint_type(request)
        limit_config = rate_limiter.limits.get(endpoint_type, rate_limiter.limits['api'])
        remaining, reset_time = rate_limiter.get_remaining_limit(request)

        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded for {endpoint_type}. Limit: {limit_config['requests']} per {limit_config['window']} seconds",
            headers={
                "X-RateLimit-Limit": str(limit_config['requests']),
                "X-RateLimit-Remaining": str(remaining),
                "X-RateLimit-Reset": str(int(time.time()) + reset_time),
                "Retry-After": str(reset_time)
            }
        )

class InMemoryUserRateLimiter:
    def __init__(self):
        self.user_limits = {
            'basic': {'requests': 100, 'window': 3600},      # Basic users: 100 requests/hour
            'premium': {'requests': 1000, 'window': 3600},   # Premium users: 1000 requests/hour
            'admin': {'requests': 5000, 'window': 3600},     # Admins: 5000 requests/hour
        }

        # In-memory storage for user rate limit counters
        # Structure: {user_id: {endpoint_type: {window: count}}}
        self.user_counters: Dict[int, Dict[str, Dict[int, int]]] = {}
        self._lock = threading.Lock()

    def check_user_limit(self, user_id: int, user_role: str, endpoint_type: str) -> bool:
        """Check if user has exceeded their rate limit"""
        try:
            limit_config = self.user_limits.get(user_role, self.user_limits['basic'])
            current_window = int(time.time()) // limit_config['window']

            with self._lock:
                # Initialize user data if not exists
                if user_id not in self.user_counters:
                    self.user_counters[user_id] = {}

                if endpoint_type not in self.user_counters[user_id]:
                    self.user_counters[user_id][endpoint_type] = {}

                # Get current count for this window
                current_count = self.user_counters[user_id][endpoint_type].get(current_window, 0)

                if current_count >= limit_config['requests']:
                    logger.warning(f"User {user_id} ({user_role}) exceeded rate limit for {endpoint_type}")
                    return False

                # Increment counter
                self.user_counters[user_id][endpoint_type][current_window] = current_count + 1

                return True

        except Exception as e:
            logger.error(f"Error checking user rate limit: {str(e)}")
            return True  # Fail open

# Global user rate limiter instance
user_rate_limiter = InMemoryUserRateLimiter()