"""
Middleware module for Web+ backend
Handles logging, error handling, and request/response processing
"""
import time
import json
import uuid
import logging
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import httpx

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for comprehensive request/response logging
    """
    
    def __init__(self, app: ASGIApp, log_body: bool = True, max_body_size: int = 1024):
        super().__init__(app)
        self.log_body = log_body
        self.max_body_size = max_body_size
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request details
        request_log = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_host": request.client.host if request.client else None,
            "headers": dict(request.headers),
        }
        
        # Log request body if enabled and not too large
        if self.log_body and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if len(body) <= self.max_body_size:
                    try:
                        request_log["body"] = json.loads(body)
                    except json.JSONDecodeError:
                        request_log["body"] = body.decode("utf-8", errors="ignore")
                else:
                    request_log["body"] = f"<Body too large: {len(body)} bytes>"
                # Re-attach body to request
                request._body = body
            except Exception as e:
                request_log["body_error"] = str(e)
        
        logger.info(f"Incoming request: {json.dumps(request_log)}")
        
        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            logger.error(f"Request {request_id} failed with exception: {str(e)}", exc_info=True)
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": str(e) if logger.isEnabledFor(logging.DEBUG) else "An error occurred",
                    "request_id": request_id
                },
                headers={"X-Request-ID": request_id}
            )
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Log response details
        response_log = {
            "request_id": request_id,
            "status_code": response.status_code,
            "process_time": f"{process_time:.3f}s",
            "headers": dict(response.headers),
        }
        
        # Add custom headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{process_time:.3f}"
        
        logger.info(f"Outgoing response: {json.dumps(response_log)}")
        
        return response


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for consistent error handling across the application
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            response = await call_next(request)
            return response
        except httpx.HTTPStatusError as e:
            # Handle external HTTP errors (e.g., from Ollama)
            logger.error(f"External HTTP error: {e}")
            return JSONResponse(
                status_code=502,
                content={
                    "error": "External service error",
                    "message": f"External service returned {e.response.status_code}",
                    "service": "ollama",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )
        except httpx.RequestError as e:
            # Handle connection errors
            logger.error(f"External connection error: {e}")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service unavailable",
                    "message": "Failed to connect to external service",
                    "service": "ollama",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )
        except ValueError as e:
            # Handle validation errors
            logger.error(f"Validation error: {e}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Validation error",
                    "message": str(e),
                    "request_id": getattr(request.state, "request_id", None)
                }
            )
        except Exception as e:
            # Handle all other errors
            logger.error(f"Unhandled error: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )


class AuthLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging authentication attempts and results
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip non-auth endpoints
        if not request.url.path.startswith("/auth"):
            return await call_next(request)
        
        # Log auth attempt
        auth_log = {
            "request_id": getattr(request.state, "request_id", None),
            "path": request.url.path,
            "method": request.method,
            "client_host": request.client.host if request.client else None,
        }
        
        # Extract username if login attempt
        if request.url.path == "/auth/login" and request.method == "POST":
            try:
                body = await request.body()
                data = json.loads(body) if body else {}
                auth_log["username"] = data.get("username", "<not provided>")
                request._body = body  # Re-attach body
            except:
                pass
        
        logger.info(f"Auth attempt: {json.dumps(auth_log)}")
        
        # Process request
        response = await call_next(request)
        
        # Log auth result
        auth_log["status_code"] = response.status_code
        auth_log["success"] = 200 <= response.status_code < 300
        
        logger.info(f"Auth result: {json.dumps(auth_log)}")
        
        return response


class CORSDebugMiddleware(BaseHTTPMiddleware):
    """
    Middleware for debugging CORS issues
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log CORS-related headers
        if "origin" in request.headers:
            logger.debug(f"CORS request from origin: {request.headers['origin']}")
            logger.debug(f"Request method: {request.method}")
            logger.debug(f"Request headers: {dict(request.headers)}")
        
        response = await call_next(request)
        
        # Log CORS response headers
        if "access-control-allow-origin" in response.headers:
            logger.debug(f"CORS response headers: {dict(response.headers)}")
        
        return response


def setup_middleware(app: ASGIApp, settings: Any) -> None:
    """
    Setup all middleware for the application
    """
    # Add middleware in reverse order (last added is executed first)
    
    # CORS debug middleware (development only)
    if settings.debug:
        app.add_middleware(CORSDebugMiddleware)
    
    # Auth logging
    app.add_middleware(AuthLoggingMiddleware)
    
    # Error handling
    app.add_middleware(ErrorHandlingMiddleware)
    
    # Request logging
    app.add_middleware(
        RequestLoggingMiddleware,
        log_body=settings.debug,
        max_body_size=1024 * 10  # 10KB
    )