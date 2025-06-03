"""
Base provider class and common interfaces for AI providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator, Union
import asyncio
import time
import logging
from datetime import datetime

from .types import (
    ProviderType,
    ProviderCredentials,
    GenerationRequest,
    GenerationResponse,
    ModelInfo,
    RateLimitInfo,
    ProviderStatus,
    StreamChunk,
    EmbeddingRequest,
    EmbeddingResponse,
    ImageGenerationRequest,
    ImageGenerationResponse
)

logger = logging.getLogger(__name__)


class ProviderError(Exception):
    """Base exception for provider errors."""
    
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None, retryable: bool = False):
        self.message = message
        self.provider = provider
        self.error_code = error_code
        self.retryable = retryable
        super().__init__(message)


class RateLimitError(ProviderError):
    """Rate limit exceeded error."""
    
    def __init__(self, message: str, provider: str, retry_after: Optional[int] = None):
        self.retry_after = retry_after
        super().__init__(message, provider, "rate_limit", retryable=True)


class AuthenticationError(ProviderError):
    """Authentication failed error."""
    
    def __init__(self, message: str, provider: str):
        super().__init__(message, provider, "authentication", retryable=False)


class ModelNotFoundError(ProviderError):
    """Model not found error."""
    
    def __init__(self, message: str, provider: str, model: str):
        self.model = model
        super().__init__(message, provider, "model_not_found", retryable=False)


class ProviderResponse:
    """Wrapper for provider responses with metadata."""
    
    def __init__(self, data: Any, metadata: Optional[Dict[str, Any]] = None):
        self.data = data
        self.metadata = metadata or {}
        self.timestamp = datetime.utcnow()


class BaseProvider(ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, credentials: ProviderCredentials):
        self.credentials = credentials
        self.provider_type = credentials.provider_type
        self._client = None
        self._rate_limit_info = RateLimitInfo()
        self._last_request_time = 0.0
        self._request_count = 0
        self._error_count = 0
        
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        pass
    
    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable provider name."""
        pass
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider client."""
        pass
    
    @abstractmethod
    async def get_available_models(self) -> List[ModelInfo]:
        """Get list of available models."""
        pass
    
    @abstractmethod
    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using the provider."""
        pass
    
    @abstractmethod
    async def stream_text(self, request: GenerationRequest) -> AsyncGenerator[StreamChunk, None]:
        """Stream text generation using the provider."""
        pass
    
    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings (optional feature)."""
        raise NotImplementedError(f"{self.name} does not support embeddings")
    
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """Generate images (optional feature)."""
        raise NotImplementedError(f"{self.name} does not support image generation")
    
    async def health_check(self) -> ProviderStatus:
        """Check provider health status."""
        start_time = time.time()
        
        try:
            # Try to get available models as a health check
            await self.get_available_models()
            response_time = time.time() - start_time
            
            error_rate = self._error_count / max(self._request_count, 1)
            
            return ProviderStatus(
                provider=self.provider_type,
                is_available=True,
                last_check=datetime.utcnow(),
                response_time=response_time,
                error_rate=error_rate,
                rate_limit_info=self._rate_limit_info
            )
            
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return ProviderStatus(
                provider=self.provider_type,
                is_available=False,
                last_check=datetime.utcnow(),
                response_time=time.time() - start_time,
                error_rate=1.0
            )
    
    async def _make_request(self, request_func, *args, **kwargs):
        """Make a request with error handling and rate limiting."""
        self._request_count += 1
        start_time = time.time()
        
        try:
            # Basic rate limiting
            await self._handle_rate_limiting()
            
            result = await request_func(*args, **kwargs)
            self._last_request_time = time.time()
            
            return result
            
        except Exception as e:
            self._error_count += 1
            self._handle_error(e)
            raise
    
    async def _handle_rate_limiting(self):
        """Handle rate limiting logic."""
        current_time = time.time()
        
        # Basic throttling - wait if requests are too frequent
        if self._last_request_time > 0:
            time_since_last = current_time - self._last_request_time
            min_interval = 0.1  # Minimum 100ms between requests
            
            if time_since_last < min_interval:
                await asyncio.sleep(min_interval - time_since_last)
    
    def _handle_error(self, error: Exception):
        """Handle and transform provider-specific errors."""
        # This method should be overridden by specific providers
        # to transform their specific errors into our common error types
        if "rate limit" in str(error).lower():
            raise RateLimitError(str(error), self.name)
        elif "authentication" in str(error).lower() or "unauthorized" in str(error).lower():
            raise AuthenticationError(str(error), self.name)
        else:
            raise ProviderError(str(error), self.name)
    
    def _extract_rate_limit_info(self, headers: Dict[str, str]) -> RateLimitInfo:
        """Extract rate limit information from response headers."""
        # This should be overridden by specific providers
        return RateLimitInfo()
    
    def _calculate_cost(self, usage, model: str) -> float:
        """Calculate cost based on usage and model pricing."""
        # This should be overridden by specific providers with their pricing
        return 0.0
    
    async def close(self):
        """Close the provider client and cleanup resources."""
        if hasattr(self._client, 'close'):
            await self._client.close()
        self._client = None
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_type})"