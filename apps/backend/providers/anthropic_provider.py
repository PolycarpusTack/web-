"""
Anthropic Claude provider implementation.
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import time
import logging

try:
    import anthropic
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .base import (
    BaseProvider, 
    ProviderError, 
    RateLimitError, 
    AuthenticationError,
    ModelNotFoundError
)
from .types import (
    ProviderType,
    ProviderCredentials,
    GenerationRequest,
    GenerationResponse,
    ModelInfo,
    ModelCapability,
    Message,
    MessageRole,
    TokenUsage,
    StreamChunk,
    EmbeddingRequest,
    EmbeddingResponse
)

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider implementation."""
    
    def __init__(self, credentials: ProviderCredentials):
        if not ANTHROPIC_AVAILABLE:
            raise ProviderError("Anthropic library not installed. Run: pip install anthropic", "anthropic")
        
        super().__init__(credentials)
        self._client: Optional[AsyncAnthropic] = None
    
    @property
    def name(self) -> str:
        return "anthropic"
    
    @property
    def display_name(self) -> str:
        return "Anthropic"
    
    async def initialize(self) -> None:
        """Initialize Anthropic client."""
        try:
            self._client = AsyncAnthropic(
                api_key=self.credentials.api_key,
                timeout=30.0
            )
            
            # Test connection by listing models
            await self._client.models.list()
            logger.info("Anthropic provider initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic provider: {e}")
            raise AuthenticationError(f"Anthropic initialization failed: {e}", self.name)
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get available Anthropic models."""
        try:
            # Anthropic models (as of 2024)
            models_data = [
                {
                    "id": "claude-3-5-sonnet-20241022",
                    "name": "Claude 3.5 Sonnet",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.VISION],
                    "context_window": 200000,
                    "max_output_tokens": 8192,
                    "input_cost_per_1k": 0.003,
                    "output_cost_per_1k": 0.015
                },
                {
                    "id": "claude-3-opus-20240229",
                    "name": "Claude 3 Opus",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.VISION],
                    "context_window": 200000,
                    "max_output_tokens": 4096,
                    "input_cost_per_1k": 0.015,
                    "output_cost_per_1k": 0.075
                },
                {
                    "id": "claude-3-sonnet-20240229",
                    "name": "Claude 3 Sonnet",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.VISION],
                    "context_window": 200000,
                    "max_output_tokens": 4096,
                    "input_cost_per_1k": 0.003,
                    "output_cost_per_1k": 0.015
                },
                {
                    "id": "claude-3-haiku-20240307",
                    "name": "Claude 3 Haiku",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.VISION],
                    "context_window": 200000,
                    "max_output_tokens": 4096,
                    "input_cost_per_1k": 0.00025,
                    "output_cost_per_1k": 0.00125
                },
                {
                    "id": "claude-2.1",
                    "name": "Claude 2.1",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING],
                    "context_window": 200000,
                    "max_output_tokens": 4096,
                    "input_cost_per_1k": 0.008,
                    "output_cost_per_1k": 0.024
                },
                {
                    "id": "claude-2.0",
                    "name": "Claude 2.0",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING],
                    "context_window": 100000,
                    "max_output_tokens": 4096,
                    "input_cost_per_1k": 0.008,
                    "output_cost_per_1k": 0.024
                },
                {
                    "id": "claude-instant-1.2",
                    "name": "Claude Instant 1.2",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT],
                    "context_window": 100000,
                    "max_output_tokens": 4096,
                    "input_cost_per_1k": 0.0008,
                    "output_cost_per_1k": 0.0024
                }
            ]
            
            models = []
            for model_data in models_data:
                model_info = ModelInfo(
                    id=model_data["id"],
                    name=model_data["name"],
                    provider=ProviderType.ANTHROPIC,
                    capabilities=model_data["capabilities"],
                    context_window=model_data["context_window"],
                    max_output_tokens=model_data["max_output_tokens"],
                    input_cost_per_1k=model_data["input_cost_per_1k"],
                    output_cost_per_1k=model_data["output_cost_per_1k"],
                    supports_streaming=True,
                    supports_functions=False,  # Anthropic doesn't use function calling like OpenAI
                    supports_vision=ModelCapability.VISION in model_data["capabilities"],
                    is_available=True
                )
                models.append(model_info)
            
            return models
            
        except Exception as e:
            self._handle_error(e)
    
    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Anthropic Claude."""
        start_time = time.time()
        
        try:
            # Convert our format to Anthropic format
            anthropic_request = self._convert_to_anthropic_request(request)
            
            if request.stream:
                # For streaming, collect all chunks
                chunks = []
                async for chunk in self.stream_text(request):
                    chunks.append(chunk.delta)
                
                content = ''.join(chunks)
                usage = TokenUsage()  # We'll estimate this
                
            else:
                # Standard completion
                response = await self._client.messages.create(**anthropic_request)
                
                # Extract content from response
                content = ""
                if response.content:
                    for content_block in response.content:
                        if hasattr(content_block, 'text'):
                            content += content_block.text
                
                # Extract usage information
                usage = TokenUsage(
                    prompt_tokens=response.usage.input_tokens if response.usage else 0,
                    completion_tokens=response.usage.output_tokens if response.usage else 0,
                    total_tokens=(response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0
                )
                
                finish_reason = response.stop_reason
            
            response_time = time.time() - start_time
            
            # Calculate cost
            cost = self._calculate_cost(usage, request.model)
            
            return GenerationResponse(
                content=content,
                model=request.model,
                provider=ProviderType.ANTHROPIC,
                finish_reason=finish_reason,
                usage=usage,
                function_call=None,  # Anthropic doesn't use function calling
                tool_calls=None,
                response_time=response_time,
                cost=cost,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            self._handle_error(e)
    
    async def stream_text(self, request: GenerationRequest) -> AsyncGenerator[StreamChunk, None]:
        """Stream text generation using Anthropic Claude."""
        try:
            anthropic_request = self._convert_to_anthropic_request(request)
            anthropic_request['stream'] = True
            
            stream = await self._client.messages.create(**anthropic_request)
            
            async for chunk in stream:
                if chunk.type == 'content_block_delta':
                    if hasattr(chunk.delta, 'text'):
                        yield StreamChunk(
                            delta=chunk.delta.text,
                            finish_reason=None,
                            metadata={'chunk': chunk.model_dump() if hasattr(chunk, 'model_dump') else None}
                        )
                elif chunk.type == 'message_stop':
                    yield StreamChunk(
                        delta="",
                        finish_reason=chunk.stop_reason if hasattr(chunk, 'stop_reason') else "stop",
                        metadata={'chunk': chunk.model_dump() if hasattr(chunk, 'model_dump') else None}
                    )
                    
        except Exception as e:
            self._handle_error(e)
    
    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings - Anthropic doesn't provide embeddings API."""
        raise ProviderError("Anthropic does not provide embeddings API", self.name)
    
    def _convert_to_anthropic_request(self, request: GenerationRequest) -> Dict[str, Any]:
        """Convert our request format to Anthropic format."""
        anthropic_request = {
            'model': request.model,
            'max_tokens': request.max_tokens or 4096,
        }
        
        # Handle messages
        if request.messages:
            # Convert messages to Anthropic format
            messages = []
            system_prompt = None
            
            for msg in request.messages:
                if msg.role == MessageRole.SYSTEM:
                    system_prompt = msg.content
                else:
                    messages.append({
                        'role': msg.role.value,
                        'content': msg.content
                    })
            
            anthropic_request['messages'] = messages
            if system_prompt:
                anthropic_request['system'] = system_prompt
        else:
            # Legacy prompt format - convert to message
            anthropic_request['messages'] = [
                {'role': 'user', 'content': request.prompt}
            ]
        
        # Optional parameters
        if request.temperature is not None:
            anthropic_request['temperature'] = request.temperature
        if request.top_p is not None:
            anthropic_request['top_p'] = request.top_p
        if request.stop:
            anthropic_request['stop_sequences'] = request.stop if isinstance(request.stop, list) else [request.stop]
        
        # Add extra parameters
        if request.extra_params:
            anthropic_request.update(request.extra_params)
        
        return anthropic_request
    
    def _calculate_cost(self, usage: TokenUsage, model: str) -> float:
        """Calculate cost based on usage."""
        # Anthropic pricing (per 1K tokens)
        pricing_map = {
            'claude-3-5-sonnet-20241022': {'input': 0.003, 'output': 0.015},
            'claude-3-opus-20240229': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet-20240229': {'input': 0.003, 'output': 0.015},
            'claude-3-haiku-20240307': {'input': 0.00025, 'output': 0.00125},
            'claude-2.1': {'input': 0.008, 'output': 0.024},
            'claude-2.0': {'input': 0.008, 'output': 0.024},
            'claude-instant-1.2': {'input': 0.0008, 'output': 0.0024},
        }
        
        pricing = pricing_map.get(model, {'input': 0.008, 'output': 0.024})
        
        input_cost = (usage.prompt_tokens / 1000) * pricing['input']
        output_cost = (usage.completion_tokens / 1000) * pricing['output']
        
        return input_cost + output_cost
    
    def _handle_error(self, error: Exception):
        """Handle Anthropic-specific errors."""
        error_str = str(error).lower()
        
        if hasattr(error, 'status_code'):
            if error.status_code == 401:
                raise AuthenticationError(f"Anthropic authentication failed: {error}", self.name)
            elif error.status_code == 404:
                raise ModelNotFoundError(f"Anthropic model not found: {error}", self.name, "unknown")
            elif error.status_code == 429:
                retry_after = getattr(error, 'retry_after', None)
                raise RateLimitError(f"Anthropic rate limit exceeded: {error}", self.name, retry_after)
        
        if 'rate limit' in error_str or 'too many requests' in error_str:
            raise RateLimitError(f"Anthropic rate limit: {error}", self.name)
        elif 'unauthorized' in error_str or 'invalid api key' in error_str:
            raise AuthenticationError(f"Anthropic authentication error: {error}", self.name)
        elif 'not found' in error_str:
            raise ModelNotFoundError(f"Anthropic model not found: {error}", self.name, "unknown")
        else:
            raise ProviderError(f"Anthropic error: {error}", self.name)