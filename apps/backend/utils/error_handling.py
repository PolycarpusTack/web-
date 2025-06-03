"""
Error handling and validation utilities for the API.
This module provides consistent error handling and input validation.
"""

from fastapi import HTTPException, status, Request
from pydantic import BaseModel, ValidationError
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Generic
import logging
from enum import Enum
import uuid
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
import json

# Set up logging
logger = logging.getLogger(__name__)

# Custom error codes
class ErrorCode(str, Enum):
    INVALID_CREDENTIALS = "invalid_credentials"
    INVALID_TOKEN = "invalid_token"
    EXPIRED_TOKEN = "expired_token"
    PERMISSION_DENIED = "permission_denied"
    RESOURCE_NOT_FOUND = "resource_not_found"
    RESOURCE_EXISTS = "resource_exists"
    INVALID_INPUT = "invalid_input"
    VALIDATION_ERROR = "validation_error"
    DATABASE_ERROR = "database_error"
    EXTERNAL_API_ERROR = "external_api_error"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    FILE_TOO_LARGE = "file_too_large"
    UNSUPPORTED_FILE_TYPE = "unsupported_file_type"
    MODEL_NOT_RUNNING = "model_not_running"
    MODEL_ERROR = "model_error"
    BACKGROUND_TASK_FAILED = "background_task_failed"
    AUTHENTICATION_REQUIRED = "authentication_required"

# Standard API error response
class ErrorResponse(BaseModel):
    error: str
    message: str
    code: str
    details: Optional[Dict[str, Any]] = None

# Typed generic APIResult
T = TypeVar('T')

class APIResult(Generic[T]):
    """
    A structured result object for API operations.
    This helps enforce consistent error handling across the application.
    """
    
    def __init__(
        self,
        success: bool = True,
        data: Optional[T] = None,
        error: Optional[str] = None,
        error_code: Optional[str] = None,
        status_code: int = status.HTTP_200_OK,
        details: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert the result to a dictionary for response."""
        if self.success:
            return {"success": True, "data": self.data}
        else:
            return {
                "success": False,
                "error": self.error,
                "code": self.error_code,
                "details": self.details
            }
            
    @classmethod
    def success(cls, data: T) -> 'APIResult[T]':
        """Create a successful result with data."""
        return cls(success=True, data=data)
        
    @classmethod
    def failure(
        cls,
        error: str,
        error_code: str = ErrorCode.INTERNAL_SERVER_ERROR,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ) -> 'APIResult':
        """Create a failure result with error information."""
        return cls(
            success=False,
            error=error,
            error_code=error_code,
            status_code=status_code,
            details=details
        )
        
    def raise_if_error(self) -> T:
        """Raise an HTTPException if this is an error result, otherwise return the data."""
        if not self.success:
            # Log the error
            logger.error(
                f"API Error: {self.error}",
                extra={
                    "error_code": self.error_code,
                    "details": self.details
                }
            )
            
            # Raise HTTPException
            raise HTTPException(
                status_code=self.status_code,
                detail=ErrorResponse(
                    error=self.error,
                    message=self.error,
                    code=self.error_code,
                    details=self.details
                ).dict()
            )
            
        return self.data

# Validation utilities
class ValidationUtil:
    """Utility methods for input validation."""
    
    @staticmethod
    def validate_model(schema_class: Type[BaseModel], data: Dict[str, Any]) -> Union[BaseModel, APIResult]:
        """
        Validate input data against a Pydantic model.
        
        Args:
            schema_class: The Pydantic model class to validate against
            data: The data to validate
            
        Returns:
            Either a validated model instance or an APIResult with validation errors
        """
        try:
            return schema_class(**data)
        except ValidationError as e:
            # Transform Pydantic validation errors into a more user-friendly format
            validation_errors = {}
            for error in e.errors():
                location = ".".join(str(loc) for loc in error["loc"])
                validation_errors[location] = error["msg"]
                
            return APIResult.failure(
                error="Validation error",
                error_code=ErrorCode.VALIDATION_ERROR,
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                details={"validation_errors": validation_errors}
            )

# Exception handlers
async def validation_exception_handler(request: Request, exc: ValidationError):
    """
    Handle Pydantic validation errors.
    
    Args:
        request: The FastAPI request
        exc: The validation error
        
    Returns:
        A structured error response
    """
    # Transform Pydantic validation errors
    validation_errors = {}
    for error in exc.errors():
        location = ".".join(str(loc) for loc in error["loc"])
        validation_errors[location] = error["msg"]
        
    # Log the error
    logger.warning(
        f"Validation error: {str(exc)}",
        extra={
            "path": request.url.path,
            "validation_errors": validation_errors
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorResponse(
            error="Validation error",
            message="Input validation failed",
            code=ErrorCode.VALIDATION_ERROR,
            details={"validation_errors": validation_errors}
        ).dict()
    )

# Database error handling
class DatabaseErrorWrapper:
    """
    A context manager for handling database operation errors.
    
    Example usage:
    ```
    async def get_user(user_id: str):
        with DatabaseErrorWrapper() as db_error:
            user = await db.execute(select(User).where(User.id == user_id))
            if db_error:
                return APIResult.failure(
                    error=str(db_error),
                    error_code=ErrorCode.DATABASE_ERROR
                )
            return APIResult.success(user)
    ```
    """
    
    def __init__(self):
        self.error = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            # Log the database error
            logger.error(
                f"Database error: {str(exc_val)}",
                exc_info=(exc_type, exc_val, exc_tb)
            )
            
            # Save the error
            self.error = exc_val
            
            # Prevent the exception from propagating
            return True
            
        return False
        
    def __bool__(self):
        """Allow the context manager to be used in a boolean context."""
        return self.error is not None
        
    def __str__(self):
        """Return the error message."""
        return str(self.error) if self.error else ""

# API key validation
def validate_api_key(api_key: str, valid_keys: List[str]) -> bool:
    """
    Validate an API key against a list of valid keys.
    
    Args:
        api_key: The API key to validate
        valid_keys: List of valid API keys
        
    Returns:
        True if the API key is valid, False otherwise
    """
    return api_key in valid_keys

# Request logging middleware
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all API requests and responses.
    
    This middleware logs:
    - Request method, path, and query parameters
    - Request processing time
    - Response status code
    - Any errors that occurred
    
    It also handles unhandled exceptions, returning a structured error response.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Generate a request ID for tracking
        request_id = str(uuid.uuid4())
        
        # Start timing the request
        start_time = time.time()
        
        # Extract basic request information
        method = request.method
        path = request.url.path
        query_params = dict(request.query_params)
        
        # Log the incoming request
        logger.info(
            f"Request started: {method} {path}",
            extra={
                "request_id": request_id,
                "method": method,
                "path": path,
                "query_params": query_params
            }
        )
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate the processing time
            processing_time = time.time() - start_time
            
            # Log the successful response
            logger.info(
                f"Request completed: {method} {path}",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "status_code": response.status_code,
                    "processing_time": processing_time
                }
            )
            
            return response
            
        except Exception as exc:
            # Calculate the processing time
            processing_time = time.time() - start_time
            
            # Log the error
            logger.error(
                f"Unhandled exception in request: {method} {path}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": path,
                    "processing_time": processing_time,
                    "error": str(exc)
                }
            )
            
            # Return a structured error response
            error_response = ErrorResponse(
                error="Internal server error",
                message="An unexpected error occurred",
                code=ErrorCode.INTERNAL_SERVER_ERROR
            )
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=error_response.dict()
            )

def register_exception_handlers(app: FastAPI):
    """
    Register all exception handlers with a FastAPI application.
    
    Args:
        app: The FastAPI application instance
    """
    # Register the validation exception handler
    app.exception_handler(ValidationError)(validation_exception_handler)
    
    # Add the request logging middleware
    app.add_middleware(RequestLoggingMiddleware)
