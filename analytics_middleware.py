"""
Custom Analytics Middleware for FastAPI Backend

This middleware provides basic analytics tracking for API requests,
serving as an alternative to Vercel Web Analytics (which is frontend-only).

Tracks:
- Request counts per endpoint
- Response times
- Status codes
- Request methods
- Client information
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("analytics")


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and log API analytics.

    In production, you can extend this to send data to:
    - External analytics services (PostHog, Mixpanel, etc.)
    - Your own database for custom analytics
    - Cloud monitoring services (DataDog, New Relic, etc.)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.request_count = 0

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Track request start time
        start_time = time.time()

        # Increment request counter
        self.request_count += 1

        # Extract request information
        method = request.method
        path = request.url.path
        client_host = request.client.host if request.client else "unknown"

        # Process the request
        try:
            response = await call_next(request)
            status_code = response.status_code
            success = True
        except Exception as e:
            # Log errors
            logger.error(f"Request failed: {method} {path} - Error: {str(e)}")
            status_code = 500
            success = False
            raise
        finally:
            # Calculate response time
            process_time = time.time() - start_time

            # Log analytics data
            if success:
                logger.info(
                    f"Analytics | "
                    f"Method: {method} | "
                    f"Path: {path} | "
                    f"Status: {status_code} | "
                    f"Duration: {process_time:.3f}s | "
                    f"Client: {client_host} | "
                    f"Total Requests: {self.request_count}"
                )

            # You can extend this to send data to external services:
            # await self._send_to_analytics_service({
            #     "method": method,
            #     "path": path,
            #     "status_code": status_code,
            #     "duration_ms": process_time * 1000,
            #     "client_ip": client_host,
            #     "user_agent": user_agent,
            #     "timestamp": time.time()
            # })

        return response

    # Uncomment and implement if using external analytics service
    # async def _send_to_analytics_service(self, data: dict):
    #     """
    #     Send analytics data to external service.
    #     Examples: PostHog, Mixpanel, Custom API, Database, etc.
    #     """
    #     pass
