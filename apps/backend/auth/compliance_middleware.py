"""
Compliance Middleware
Automatically logs requests and responses for audit and compliance purposes.
"""

import time
import json
import logging
from typing import Callable, Optional, Dict, Any
from fastapi import Request, Response
from fastapi.responses import StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import asyncio

from db.database import async_session_maker
from .compliance_router import create_enhanced_audit_log

logger = logging.getLogger(__name__)


class ComplianceMiddleware(BaseHTTPMiddleware):
    """Middleware to automatically log requests for compliance and audit purposes."""
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        
        # Default configuration
        self.log_requests = self.config.get("log_requests", True)
        self.log_responses = self.config.get("log_responses", False)
        self.log_request_body = self.config.get("log_request_body", False)
        self.log_response_body = self.config.get("log_response_body", False)
        self.exclude_paths = set(self.config.get("exclude_paths", [
            "/health", "/metrics", "/docs", "/openapi.json", "/favicon.ico"
        ]))
        self.exclude_methods = set(self.config.get("exclude_methods", ["OPTIONS"]))
        self.sensitive_headers = set(self.config.get("sensitive_headers", [
            "authorization", "cookie", "x-api-key", "x-auth-token"
        ]))
        self.max_body_size = self.config.get("max_body_size", 10000)  # 10KB
        
        # Risk assessment configuration
        self.high_risk_paths = set(self.config.get("high_risk_paths", [
            "/auth/", "/rbac/", "/workspaces/", "/compliance/", "/admin/"
        ]))
        self.data_access_paths = set(self.config.get("data_access_paths", [
            "/conversations/", "/files/", "/export/", "/download/"
        ]))
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and response for compliance logging."""
        
        # Skip excluded paths and methods
        if (request.url.path in self.exclude_paths or 
            any(request.url.path.startswith(path) for path in self.exclude_paths) or
            request.method in self.exclude_methods):
            return await call_next(request)
        
        # Start timing
        start_time = time.time()
        
        # Extract request information
        request_info = await self._extract_request_info(request)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            response_time = time.time() - start_time
            
            # Extract response information
            response_info = await self._extract_response_info(response)
            
            # Log to audit system (non-blocking)
            asyncio.create_task(self._log_audit_entry(request, request_info, response_info, response_time))
            
            return response
            
        except Exception as e:
            # Log failed requests
            response_time = time.time() - start_time
            error_info = {
                "error": str(e),
                "error_type": type(e).__name__
            }
            
            asyncio.create_task(self._log_audit_entry(request, request_info, error_info, response_time, is_error=True))
            raise
    
    async def _extract_request_info(self, request: Request) -> Dict[str, Any]:
        """Extract relevant information from the request."""
        info = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": self._sanitize_headers(dict(request.headers)),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length")
        }
        
        # Extract request body if configured and not too large
        if (self.log_request_body and 
            request.method in ["POST", "PUT", "PATCH"] and
            "application/json" in (request.headers.get("content-type", ""))):
            
            try:
                content_length = int(request.headers.get("content-length", 0))
                if content_length <= self.max_body_size:
                    # Read body (this consumes the stream, so we need to restore it)
                    body = await request.body()
                    if body:
                        try:
                            info["body"] = json.loads(body.decode())
                        except (json.JSONDecodeError, UnicodeDecodeError):
                            info["body"] = "<binary_or_invalid_json>"
            except Exception as e:
                logger.warning(f"Failed to extract request body: {e}")
        
        return info
    
    async def _extract_response_info(self, response: Response) -> Dict[str, Any]:
        """Extract relevant information from the response."""
        info = {
            "status_code": response.status_code,
            "headers": self._sanitize_headers(dict(response.headers)),
            "content_type": response.headers.get("content-type")
        }
        
        # For streaming responses, we can't easily access the body
        if isinstance(response, StreamingResponse):
            info["response_type"] = "streaming"
        else:
            info["response_type"] = "standard"
            
            # Extract response body if configured and not too large
            if (self.log_response_body and 
                response.status_code < 300 and
                "application/json" in (response.headers.get("content-type", ""))):
                
                try:
                    # This is tricky with FastAPI responses
                    # For now, we'll skip response body logging to avoid complexity
                    pass
                except Exception as e:
                    logger.warning(f"Failed to extract response body: {e}")
        
        return info
    
    def _sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Remove or mask sensitive headers."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized
    
    def _assess_request_risk(self, request: Request, request_info: Dict[str, Any]) -> str:
        """Assess the risk level of a request."""
        risk_level = "low"
        
        # High-risk paths
        if any(request.url.path.startswith(path) for path in self.high_risk_paths):
            risk_level = "medium"
        
        # Data access paths
        if any(request.url.path.startswith(path) for path in self.data_access_paths):
            risk_level = "medium"
        
        # Administrative actions
        if request.method in ["DELETE", "PUT"] and "admin" in request.url.path.lower():
            risk_level = "high"
        
        # Bulk operations
        if "bulk" in request.url.path.lower() or "export" in request.url.path.lower():
            risk_level = "high"
        
        return risk_level
    
    def _determine_action(self, request: Request) -> str:
        """Determine the action being performed."""
        method_mapping = {
            "GET": "read",
            "POST": "create", 
            "PUT": "update",
            "PATCH": "update",
            "DELETE": "delete"
        }
        
        base_action = method_mapping.get(request.method, "unknown")
        
        # Special cases
        if "login" in request.url.path:
            return "login"
        elif "logout" in request.url.path:
            return "logout"
        elif "export" in request.url.path:
            return "export"
        elif "download" in request.url.path:
            return "download"
        elif "upload" in request.url.path:
            return "upload"
        elif "invite" in request.url.path:
            return "invite"
        
        return base_action
    
    def _determine_resource_type(self, request: Request) -> str:
        """Determine the resource type being accessed."""
        path = request.url.path.lower()
        
        # Extract resource type from path
        if "/conversations" in path:
            return "conversations"
        elif "/workspaces" in path:
            return "workspaces"
        elif "/users" in path or "/rbac" in path:
            return "users"
        elif "/files" in path:
            return "files"
        elif "/pipelines" in path:
            return "pipelines"
        elif "/models" in path:
            return "models"
        elif "/auth" in path:
            return "authentication"
        elif "/compliance" in path or "/audit" in path:
            return "compliance"
        else:
            return "system"
    
    async def _get_user_id_from_request(self, request: Request) -> Optional[str]:
        """Extract user ID from request (if authenticated)."""
        try:
            # Try to get user from JWT token
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # This would require importing JWT utilities
                # For now, we'll return None and rely on the application to set user context
                pass
            
            # Try to get from API key
            api_key = request.headers.get("x-api-key")
            if api_key:
                # This would require looking up the API key
                # For now, we'll return None
                pass
                
        except Exception as e:
            logger.warning(f"Failed to extract user ID: {e}")
        
        return None
    
    async def _log_audit_entry(
        self, 
        request: Request, 
        request_info: Dict[str, Any], 
        response_info: Dict[str, Any], 
        response_time: float,
        is_error: bool = False
    ):
        """Log the request/response to the audit system."""
        try:
            async with async_session_maker() as db:
                # Determine action and resource type
                action = self._determine_action(request)
                resource_type = self._determine_resource_type(request)
                
                # Add error suffix if request failed
                if is_error:
                    action = f"{action}_failed"
                
                # Assess risk
                risk_level = self._assess_request_risk(request, request_info)
                
                # Get user ID (this would need to be enhanced with proper auth integration)
                user_id = await self._get_user_id_from_request(request)
                
                # Prepare metadata
                meta_data = {
                    "request": request_info,
                    "response": response_info,
                    "response_time_ms": round(response_time * 1000, 2),
                    "compliance_log": True
                }
                
                # Create audit log entry
                await create_enhanced_audit_log(
                    db=db,
                    user_id=user_id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=None,  # Would need to extract from path parameters
                    workspace_id=None,  # Would need to extract from request context
                    request=request,
                    meta_data=meta_data
                )
                
        except Exception as e:
            logger.error(f"Failed to log audit entry: {e}")


# Compliance middleware configuration for different environments
DEVELOPMENT_CONFIG = {
    "log_requests": True,
    "log_responses": False,
    "log_request_body": True,
    "log_response_body": False,
    "exclude_paths": ["/health", "/metrics", "/docs", "/openapi.json", "/favicon.ico"],
    "max_body_size": 5000
}

PRODUCTION_CONFIG = {
    "log_requests": True,
    "log_responses": True,
    "log_request_body": False,  # More restrictive in production
    "log_response_body": False,
    "exclude_paths": ["/health", "/metrics"],
    "max_body_size": 1000
}

SOX_COMPLIANCE_CONFIG = {
    "log_requests": True,
    "log_responses": True,
    "log_request_body": True,
    "log_response_body": True,
    "exclude_paths": ["/health"],  # Minimal exclusions for SOX
    "max_body_size": 50000,  # Larger for comprehensive audit
    "high_risk_paths": [
        "/auth/", "/rbac/", "/workspaces/", "/compliance/", "/admin/",
        "/financial/", "/reporting/", "/export/"
    ]
}