"""
Error Handling Middleware - Centralized error processing
"""

import logging
import traceback
from typing import Callable
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling and logging"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            return await self.handle_exception(request, exc)
    
    async def handle_exception(self, request: Request, exc: Exception) -> JSONResponse:
        """Handle and format exceptions"""
        
        # Generate correlation ID for error tracking
        correlation_id = f"err_{int(time.time() * 1000)}"
        
        # Log the error with full traceback
        logger.error(
            f"Request failed [{correlation_id}]: {request.method} {request.url} - {exc}",
            extra={
                "correlation_id": correlation_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
                "traceback": traceback.format_exc()
            }
        )
        
        # Determine response based on environment
        if settings.is_development:
            # Detailed error response for development
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "detail": str(exc),
                    "type": type(exc).__name__,
                    "correlation_id": correlation_id,
                    "traceback": traceback.format_exc().split("\n") if settings.DEBUG else None
                }
            )
        else:
            # Generic error response for production
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "correlation_id": correlation_id
                }
            )