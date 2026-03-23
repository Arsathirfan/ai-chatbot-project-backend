# Backend Analytics Implementation

## Overview

This FastAPI backend includes custom analytics middleware to track API usage and performance metrics. 

**Note:** Vercel Web Analytics (`@vercel/analytics`) is designed exclusively for frontend/browser-based applications and cannot be used with backend-only projects like this FastAPI service.

## What's Tracked

The analytics middleware automatically monitors:

- **Request Count**: Total number of API requests
- **Response Time**: Duration for each request (in seconds)
- **Endpoint Usage**: Which API endpoints are being called
- **Status Codes**: Success/error rates
- **Client Information**: IP addresses and User-Agent strings
- **Methods**: HTTP methods (GET, POST, etc.)

## Configuration

Analytics can be configured via environment variables in your `.env` file:

```env
# Enable/disable analytics (default: true)
ENABLE_ANALYTICS=true

# Set logging level (default: INFO)
ANALYTICS_LOG_LEVEL=INFO

# Optional: External analytics service
ANALYTICS_EXTERNAL_ENDPOINT=https://your-analytics-service.com/api/events
ANALYTICS_API_KEY=your_analytics_api_key_here
```

## Usage

### Viewing Analytics Locally

When running the FastAPI server locally, analytics data is logged to the console:

```bash
2026-03-23 10:30:15 - analytics - INFO - Analytics | Method: POST | Path: /rag/search | Status: 200 | Duration: 0.345s | Client: 127.0.0.1 | Total Requests: 15
```

### Viewing Analytics in Production (Vercel)

On Vercel, you have multiple options:

1. **Vercel Observability Dashboard** (Built-in, No Setup Required)
   - Navigate to your project in Vercel dashboard
   - Go to the "Observability" tab
   - View Function Invocations, errors, and performance metrics
   - Available on all Vercel plans

2. **Vercel Logs**
   - View real-time logs in the Vercel dashboard
   - Filter by function, time range, and status
   - Analytics middleware logs will appear here

### Extending to External Services

To send analytics data to external services, uncomment and implement the `_send_to_analytics_service` method in `analytics_middleware.py`:

```python
async def _send_to_analytics_service(self, data: dict):
    """Send analytics data to external service."""
    import httpx
    
    if analytics_config.has_external_service:
        async with httpx.AsyncClient() as client:
            await client.post(
                analytics_config.external_endpoint,
                json=data,
                headers={"Authorization": f"Bearer {analytics_config.api_key}"}
            )
```

## Popular Analytics Integration Options

If you need more advanced analytics, consider integrating:

### 1. **PostHog** (Open Source Product Analytics)
```bash
pip install posthog
```

### 2. **Mixpanel** (Product Analytics)
```bash
pip install mixpanel
```

### 3. **Sentry** (Error Tracking & Performance Monitoring)
```bash
pip install sentry-sdk[fastapi]
```

### 4. **OpenTelemetry** (Distributed Tracing)
```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi
```

### 5. **Custom Database Storage**
Store analytics in PostgreSQL or similar database for custom dashboards

## Architecture

```
Request → AnalyticsMiddleware → FastAPI Endpoint → Response
              ↓
         Log Analytics Data
              ↓
    [Console / External Service / Database]
```

## Benefits

- **Zero Dependencies**: Uses only Python standard library + FastAPI
- **Lightweight**: Minimal performance overhead
- **Flexible**: Easy to extend for external services
- **Privacy-Friendly**: Data stays in your logs by default
- **Production-Ready**: Works seamlessly on Vercel

## Disabling Analytics

To disable analytics, set the environment variable:

```env
ENABLE_ANALYTICS=false
```

Or remove the middleware from `main.py`.

## Next Steps

1. Deploy to Vercel to see analytics in the Observability dashboard
2. Optionally integrate with external analytics services
3. Create custom dashboards based on logged data
4. Set up alerts for error rates or slow endpoints

## Support

For questions or issues with the analytics implementation, refer to:
- [FastAPI Middleware Documentation](https://fastapi.tiangolo.com/tutorial/middleware/)
- [Vercel Observability](https://vercel.com/docs/observability)
- [Vercel Functions Logs](https://vercel.com/docs/observability/runtime-logs)
