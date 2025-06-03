"""
Security Hardening Middleware for Web+ Backend

This module implements comprehensive security measures to protect
our Ferrari from attacks while maintaining peak performance.
"""
import time
import hashlib
import secrets
from typing import Dict, Any, Optional, Set
from collections import defaultdict, deque
from datetime import datetime, timedelta

from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import ipaddress


class SecurityHeaders:
    """Security headers for HTTP responses."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get comprehensive security headers."""
        return {
            # HTTPS enforcement
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # Content type protection
            "X-Content-Type-Options": "nosniff",
            
            # Frame protection
            "X-Frame-Options": "DENY",
            
            # XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "connect-src 'self' ws: wss:; "
                "font-src 'self'; "
                "object-src 'none'; "
                "media-src 'self'; "
                "frame-src 'none';"
            ),
            
            # Feature policy
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=(), "
                "payment=(), "
                "usb=()"
            ),
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Cache control for sensitive data
            "Cache-Control": "no-store, no-cache, must-revalidate, proxy-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            
            # Server identification
            "Server": "Web+ API",
            
            # Cross-domain policies
            "X-Permitted-Cross-Domain-Policies": "none"
        }


class RateLimiter:
    """Advanced rate limiting with multiple strategies."""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
        self.suspicious_patterns: Set[str] = set()
        
        # Rate limit configurations
        self.limits = {
            "per_minute": 60,
            "per_hour": 1000,
            "per_day": 10000,
            "burst_limit": 10,  # Max requests in 1 second
        }
        
        # Adaptive limits for different endpoints
        self.endpoint_limits = {
            "/auth/login": {"per_minute": 5, "per_hour": 20},
            "/auth/register": {"per_minute": 3, "per_hour": 10},
            "/api/chat/completions": {"per_minute": 30, "per_hour": 500},
            "/api/pipelines/execute": {"per_minute": 10, "per_hour": 100},
        }
    
    def is_allowed(self, client_ip: str, endpoint: str) -> tuple[bool, Optional[str]]:
        """Check if request is allowed based on rate limits."""
        now = datetime.now()
        client_key = f"{client_ip}:{endpoint}"
        
        # Check if IP is temporarily blocked
        if client_ip in self.blocked_ips:
            if now < self.blocked_ips[client_ip]:
                return False, "IP temporarily blocked due to suspicious activity"
            else:
                del self.blocked_ips[client_ip]
        
        # Clean old requests
        self._cleanup_old_requests(client_key, now)
        
        # Get applicable limits
        limits = self.endpoint_limits.get(endpoint, self.limits)
        
        # Check burst limit (1 second window)
        recent_requests = [t for t in self.requests[client_key] 
                          if (now - t).total_seconds() <= 1]
        if len(recent_requests) >= self.limits["burst_limit"]:
            self._mark_suspicious(client_ip, "burst_limit_exceeded")
            return False, "Too many requests in short time"
        
        # Check per-minute limit
        minute_requests = [t for t in self.requests[client_key] 
                          if (now - t).total_seconds() <= 60]
        if len(minute_requests) >= limits.get("per_minute", self.limits["per_minute"]):
            return False, "Rate limit exceeded: too many requests per minute"
        
        # Check per-hour limit
        hour_requests = [t for t in self.requests[client_key] 
                        if (now - t).total_seconds() <= 3600]
        if len(hour_requests) >= limits.get("per_hour", self.limits["per_hour"]):
            return False, "Rate limit exceeded: too many requests per hour"
        
        # Record this request
        self.requests[client_key].append(now)
        
        return True, None
    
    def _cleanup_old_requests(self, client_key: str, now: datetime):
        """Remove requests older than 24 hours."""
        cutoff = now - timedelta(hours=24)
        while (self.requests[client_key] and 
               self.requests[client_key][0] < cutoff):
            self.requests[client_key].popleft()
    
    def _mark_suspicious(self, client_ip: str, reason: str):
        """Mark IP as suspicious and potentially block it."""
        pattern_key = f"{client_ip}:{reason}"
        self.suspicious_patterns.add(pattern_key)
        
        # Block IP for 15 minutes after multiple suspicious activities
        suspicious_count = len([p for p in self.suspicious_patterns 
                               if p.startswith(client_ip)])
        if suspicious_count >= 3:
            self.blocked_ips[client_ip] = datetime.now() + timedelta(minutes=15)


class InputSanitizer:
    """Input sanitization and validation."""
    
    def __init__(self):
        self.dangerous_patterns = [
            r"<script[^>]*>.*?</script>",  # XSS scripts
            r"javascript:",  # JavaScript URLs
            r"on\w+\s*=",  # Event handlers
            r"expression\s*\(",  # CSS expressions
            r"vbscript:",  # VBScript URLs
            r"data:text/html",  # Data URLs with HTML
            r"\bUNION\b.*\bSELECT\b",  # SQL injection
            r"\bDROP\b.*\bTABLE\b",  # SQL DROP
            r"\bINSERT\b.*\bINTO\b",  # SQL INSERT
            r"\bDELETE\b.*\bFROM\b",  # SQL DELETE
            r"\.\.\/",  # Path traversal
            r"\.\.\\",  # Path traversal (Windows)
        ]
    
    def sanitize_input(self, data: Any) -> Any:
        """Sanitize input data recursively."""
        if isinstance(data, str):
            return self._sanitize_string(data)
        elif isinstance(data, dict):
            return {key: self.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        else:
            return data
    
    def _sanitize_string(self, text: str) -> str:
        """Sanitize a string value."""
        import re
        import html
        
        # HTML encode to prevent XSS
        text = html.escape(text)
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Check for dangerous patterns
        for pattern in self.dangerous_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Input contains potentially dangerous content"
                )
        
        return text
    
    def validate_file_upload(self, filename: str, content_type: str) -> bool:
        """Validate file upload safety."""
        import mimetypes
        
        # Check file extension
        allowed_extensions = {
            '.txt', '.pdf', '.doc', '.docx', '.xls', '.xlsx', 
            '.ppt', '.pptx', '.jpg', '.jpeg', '.png', '.gif', 
            '.csv', '.json', '.md'
        }
        
        file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''
        if file_ext not in allowed_extensions:
            return False
        
        # Verify MIME type matches extension
        expected_type, _ = mimetypes.guess_type(filename)
        if expected_type and not content_type.startswith(expected_type.split('/')[0]):
            return False
        
        return True


class SecurityMiddleware(BaseHTTPMiddleware):
    """Comprehensive security middleware."""
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        self.config = config or {}
        self.rate_limiter = RateLimiter()
        self.input_sanitizer = InputSanitizer()
        self.security_headers = SecurityHeaders()
        
        # Security configurations
        self.trusted_proxies = self._parse_trusted_proxies()
        self.blocked_user_agents = {
            "curl", "wget", "python-requests", "scrapy", "bot", "crawler"
        }
    
    async def dispatch(self, request: Request, call_next):
        """Process request through security layers."""
        start_time = time.time()
        
        try:
            # 1. IP and User-Agent validation
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "").lower()
            
            # Block suspicious user agents (configurable)
            if any(blocked in user_agent for blocked in self.blocked_user_agents):
                if not self.config.get("allow_automation", False):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Access denied"}
                    )
            
            # 2. Rate limiting
            endpoint = request.url.path
            allowed, message = self.rate_limiter.is_allowed(client_ip, endpoint)
            if not allowed:
                return JSONResponse(
                    status_code=429,
                    content={"detail": message},
                    headers={"Retry-After": "60"}
                )
            
            # 3. Request size limits
            content_length = request.headers.get("content-length")
            if content_length:
                max_size = self.config.get("max_request_size", 10 * 1024 * 1024)  # 10MB
                if int(content_length) > max_size:
                    return JSONResponse(
                        status_code=413,
                        content={"detail": "Request too large"}
                    )
            
            # 4. Process request
            response = await call_next(request)
            
            # 5. Add security headers
            for header, value in self.security_headers.get_security_headers().items():
                response.headers[header] = value
            
            # 6. Add timing information (for monitoring)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Security incident logging
            await self._log_security_incident(request, str(e))
            
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
                headers=self.security_headers.get_security_headers()
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get the real client IP address."""
        # Check X-Forwarded-For header (from trusted proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP (client IP)
            client_ip = forwarded_for.split(",")[0].strip()
            try:
                ipaddress.ip_address(client_ip)
                return client_ip
            except ValueError:
                pass
        
        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            try:
                ipaddress.ip_address(real_ip)
                return real_ip
            except ValueError:
                pass
        
        # Fall back to direct connection
        return request.client.host if request.client else "unknown"
    
    def _parse_trusted_proxies(self) -> Set[str]:
        """Parse trusted proxy IP ranges."""
        proxies = self.config.get("trusted_proxies", [])
        trusted = set()
        
        for proxy in proxies:
            try:
                # Support both single IPs and CIDR ranges
                if "/" in proxy:
                    network = ipaddress.ip_network(proxy, strict=False)
                    trusted.add(str(network))
                else:
                    ip = ipaddress.ip_address(proxy)
                    trusted.add(str(ip))
            except ValueError:
                continue
        
        return trusted
    
    async def _log_security_incident(self, request: Request, error: str):
        """Log security incidents for monitoring."""
        incident = {
            "timestamp": datetime.now().isoformat(),
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", ""),
            "method": request.method,
            "url": str(request.url),
            "error": error,
            "headers": dict(request.headers)
        }
        
        # In production, send to security monitoring system
        print(f"🚨 Security Incident: {incident}")


class CSRFProtection:
    """CSRF protection for state-changing operations."""
    
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
    
    def generate_token(self, session_id: str) -> str:
        """Generate CSRF token for a session."""
        timestamp = str(int(time.time()))
        message = f"{session_id}:{timestamp}"
        signature = hashlib.hmac(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"{timestamp}:{signature}"
    
    def validate_token(self, token: str, session_id: str, max_age: int = 3600) -> bool:
        """Validate CSRF token."""
        try:
            timestamp_str, signature = token.split(":", 1)
            timestamp = int(timestamp_str)
            
            # Check token age
            if time.time() - timestamp > max_age:
                return False
            
            # Verify signature
            message = f"{session_id}:{timestamp_str}"
            expected_signature = hashlib.hmac(
                self.secret_key.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return secrets.compare_digest(signature, expected_signature)
            
        except (ValueError, TypeError):
            return False


# Rate limiting decorator for specific endpoints
def rate_limit(per_minute: int = 60, per_hour: int = 1000):
    """Decorator for endpoint-specific rate limiting."""
    def decorator(func):
        func._rate_limit = {"per_minute": per_minute, "per_hour": per_hour}
        return func
    return decorator


# Security configuration for production
PRODUCTION_SECURITY_CONFIG = {
    "max_request_size": 10 * 1024 * 1024,  # 10MB
    "allow_automation": False,
    "trusted_proxies": ["127.0.0.1", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"],
    "rate_limiting": {
        "global": {"per_minute": 60, "per_hour": 1000},
        "auth": {"per_minute": 5, "per_hour": 20},
        "api": {"per_minute": 30, "per_hour": 500}
    }
}