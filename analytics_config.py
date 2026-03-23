"""
Analytics Configuration

Configure analytics settings and optional integrations.
"""

import os
from typing import Optional


class AnalyticsConfig:
    """
    Configuration for analytics middleware.

    Environment Variables:
    - ENABLE_ANALYTICS: Enable/disable analytics (default: True)
    - ANALYTICS_LOG_LEVEL: Logging level (default: INFO)
    - ANALYTICS_EXTERNAL_ENDPOINT: Optional external service endpoint
    - ANALYTICS_API_KEY: Optional API key for external service
    """

    def __init__(self):
        self.enabled = os.getenv("ENABLE_ANALYTICS", "true").lower() == "true"
        self.log_level = os.getenv("ANALYTICS_LOG_LEVEL", "INFO")
        self.external_endpoint: Optional[str] = os.getenv("ANALYTICS_EXTERNAL_ENDPOINT")
        self.api_key: Optional[str] = os.getenv("ANALYTICS_API_KEY")

    @property
    def has_external_service(self) -> bool:
        """Check if external analytics service is configured."""
        return bool(self.external_endpoint and self.api_key)


# Global config instance
config = AnalyticsConfig()
