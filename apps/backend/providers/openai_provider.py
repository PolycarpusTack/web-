"""
OpenAI provider implementation.
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import time
import logging

try:
    import openai
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

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
    EmbeddingResponse,
    ImageGenerationRequest,
    ImageGenerationResponse
)

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, credentials: ProviderCredentials):
        if not OPENAI_AVAILABLE:
            raise ProviderError("OpenAI library not installed. Run: pip install openai", "openai")
        
        super().__init__(credentials)
        self._client: Optional[AsyncOpenAI] = None
    
    @property
    def name(self) -> str:
        return "openai"
    
    @property
    def display_name(self) -> str:
        return "OpenAI"
    
    async def initialize(self) -> None:
        """Initialize OpenAI client."""
        try:
            self._client = AsyncOpenAI(
                api_key=self.credentials.api_key,
                organization=self.credentials.organization_id,
                timeout=30.0
            )
            
            # Test connection
            await self._client.models.list()
            logger.info("OpenAI provider initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI provider: {e}")
            raise AuthenticationError(f"OpenAI initialization failed: {e}", self.name)
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get available OpenAI models."""
        try:
            models_response = await self._client.models.list()
            
            models = []
            for model_data in models_response.data:
                model_id = model_data.id
                
                # Determine capabilities based on model type
                capabilities = []
                if any(name in model_id.lower() for name in ['gpt-3.5', 'gpt-4']):
                    capabilities.extend([
                        ModelCapability.TEXT_GENERATION,
                        ModelCapability.CHAT,
                        ModelCapability.CODE_GENERATION,
                        ModelCapability.REASONING
                    ])
                    
                    if 'gpt-4' in model_id.lower():
                        if 'vision' in model_id.lower():
                            capabilities.append(ModelCapability.VISION)
                        if 'turbo' in model_id.lower():
                            capabilities.append(ModelCapability.FUNCTION_CALLING)
                
                elif 'embedding' in model_id.lower():
                    capabilities.append(ModelCapability.EMBEDDINGS)
                
                elif 'dall-e' in model_id.lower():
                    capabilities.append(ModelCapability.IMAGE_GENERATION)
                
                elif 'whisper' in model_id.lower():
                    capabilities.append(ModelCapability.SPEECH_TO_TEXT)
                
                elif 'tts' in model_id.lower():
                    capabilities.append(ModelCapability.TEXT_TO_SPEECH)
                
                # Get pricing info
                pricing = self._get_model_pricing(model_id)
                
                model_info = ModelInfo(
                    id=model_id,
                    name=model_id,
                    provider=ProviderType.OPENAI,
                    capabilities=capabilities,
                    context_window=self._get_context_window(model_id),
                    max_output_tokens=self._get_max_output_tokens(model_id),
                    input_cost_per_1k=pricing.get('input', 0.0),
                    output_cost_per_1k=pricing.get('output', 0.0),
                    supports_streaming=any(cap in capabilities for cap in [
                        ModelCapability.TEXT_GENERATION,
                        ModelCapability.CHAT
                    ]),
                    supports_functions='gpt-4' in model_id.lower() or 'gpt-3.5-turbo' in model_id.lower(),
                    supports_vision='vision' in model_id.lower(),
                    is_available=True
                )
                
                models.append(model_info)
            
            return models
            
        except Exception as e:
            self._handle_error(e)
    
    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using OpenAI."""
        start_time = time.time()
        
        try:
            # Convert our format to OpenAI format
            openai_request = self._convert_to_openai_request(request)
            
            if request.stream:
                # For non-streaming, we'll collect all chunks
                chunks = []
                async for chunk in self.stream_text(request):
                    chunks.append(chunk.delta)
                
                content = ''.join(chunks)
                usage = TokenUsage()  # We'll estimate this
                
            else:
                # Standard completion
                if request.messages:
                    response = await self._client.chat.completions.create(**openai_request)
                    content = response.choices[0].message.content or ""
                    usage = TokenUsage(
                        prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                        completion_tokens=response.usage.completion_tokens if response.usage else 0,
                        total_tokens=response.usage.total_tokens if response.usage else 0
                    )
                    finish_reason = response.choices[0].finish_reason
                    function_call = getattr(response.choices[0].message, 'function_call', None)
                    tool_calls = getattr(response.choices[0].message, 'tool_calls', None)
                else:
                    # Legacy completions endpoint
                    response = await self._client.completions.create(**openai_request)
                    content = response.choices[0].text or ""
                    usage = TokenUsage(
                        prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                        completion_tokens=response.usage.completion_tokens if response.usage else 0,
                        total_tokens=response.usage.total_tokens if response.usage else 0
                    )
                    finish_reason = response.choices[0].finish_reason
                    function_call = None
                    tool_calls = None
            
            response_time = time.time() - start_time
            
            # Calculate cost
            cost = self._calculate_cost(usage, request.model)
            
            return GenerationResponse(
                content=content,
                model=request.model,
                provider=ProviderType.OPENAI,
                finish_reason=finish_reason,
                usage=usage,
                function_call=function_call,
                tool_calls=tool_calls,
                response_time=response_time,
                cost=cost,
                raw_response=response.model_dump() if hasattr(response, 'model_dump') else None
            )
            
        except Exception as e:
            self._handle_error(e)
    
    async def stream_text(self, request: GenerationRequest) -> AsyncGenerator[StreamChunk, None]:
        """Stream text generation using OpenAI."""
        try:
            openai_request = self._convert_to_openai_request(request)
            openai_request['stream'] = True
            
            if request.messages:
                stream = await self._client.chat.completions.create(**openai_request)
            else:
                stream = await self._client.completions.create(**openai_request)
            
            async for chunk in stream:
                if hasattr(chunk, 'choices') and chunk.choices:
                    choice = chunk.choices[0]
                    
                    if request.messages:
                        # Chat completion
                        delta = choice.delta
                        content = getattr(delta, 'content', '') or ''
                        finish_reason = choice.finish_reason
                    else:
                        # Legacy completion
                        content = choice.text or ''
                        finish_reason = choice.finish_reason
                    
                    yield StreamChunk(
                        delta=content,
                        finish_reason=finish_reason,
                        metadata={'chunk': chunk.model_dump() if hasattr(chunk, 'model_dump') else None}
                    )
                    
        except Exception as e:
            self._handle_error(e)
    
    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using OpenAI."""
        start_time = time.time()
        
        try:
            response = await self._client.embeddings.create(
                input=request.input,
                model=request.model,
                encoding_format=request.encoding_format,
                dimensions=request.dimensions
            )
            
            embeddings = [item.embedding for item in response.data]
            
            usage = TokenUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0
            )
            
            response_time = time.time() - start_time
            cost = self._calculate_cost(usage, request.model)
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=request.model,
                provider=ProviderType.OPENAI,
                usage=usage,
                response_time=response_time,
                cost=cost
            )
            
        except Exception as e:
            self._handle_error(e)
    
    async def generate_image(self, request: ImageGenerationRequest) -> ImageGenerationResponse:
        """Generate images using DALL-E."""
        start_time = time.time()
        
        try:
            response = await self._client.images.generate(
                prompt=request.prompt,
                model=request.model,
                size=request.size,
                quality=request.quality,
                style=request.style,
                n=request.n,
                response_format=request.response_format
            )
            
            images = []
            for image_data in response.data:
                if hasattr(image_data, 'url'):
                    images.append({'url': image_data.url})
                elif hasattr(image_data, 'b64_json'):
                    images.append({'b64_json': image_data.b64_json})
            
            response_time = time.time() - start_time
            
            # Estimate cost based on model and size
            cost = self._calculate_image_cost(request.model, request.size, request.quality, request.n)
            
            return ImageGenerationResponse(
                images=images,
                model=request.model,
                provider=ProviderType.OPENAI,
                response_time=response_time,
                cost=cost
            )
            
        except Exception as e:
            self._handle_error(e)
    
    def _convert_to_openai_request(self, request: GenerationRequest) -> Dict[str, Any]:
        """Convert our request format to OpenAI format."""
        openai_request = {
            'model': request.model,
        }
        
        if request.messages:
            # Chat completion
            openai_request['messages'] = [
                {
                    'role': msg.role.value,
                    'content': msg.content,
                    **({"name": msg.name} if msg.name else {}),
                    **({"function_call": msg.function_call} if msg.function_call else {}),
                    **({"tool_calls": msg.tool_calls} if msg.tool_calls else {})
                }
                for msg in request.messages
            ]
        else:
            # Legacy completion
            openai_request['prompt'] = request.prompt
        
        # Optional parameters
        if request.max_tokens:
            openai_request['max_tokens'] = request.max_tokens
        if request.temperature is not None:
            openai_request['temperature'] = request.temperature
        if request.top_p is not None:
            openai_request['top_p'] = request.top_p
        if request.frequency_penalty is not None:
            openai_request['frequency_penalty'] = request.frequency_penalty
        if request.presence_penalty is not None:
            openai_request['presence_penalty'] = request.presence_penalty
        if request.stop:
            openai_request['stop'] = request.stop
        if request.functions:
            openai_request['functions'] = request.functions
        if request.tools:
            openai_request['tools'] = request.tools
        if request.tool_choice:
            openai_request['tool_choice'] = request.tool_choice
        
        # Add extra parameters
        if request.extra_params:
            openai_request.update(request.extra_params)
        
        return openai_request
    
    def _get_model_pricing(self, model_id: str) -> Dict[str, float]:
        """Get pricing for a specific model."""
        # This would normally come from a database or configuration
        pricing_map = {
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-4-32k': {'input': 0.06, 'output': 0.12},
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-4-vision-preview': {'input': 0.01, 'output': 0.03},
            'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002},
            'gpt-3.5-turbo-16k': {'input': 0.003, 'output': 0.004},
            'text-embedding-ada-002': {'input': 0.0001, 'output': 0.0},
            'text-embedding-3-small': {'input': 0.00002, 'output': 0.0},
            'text-embedding-3-large': {'input': 0.00013, 'output': 0.0},
        }
        
        return pricing_map.get(model_id, {'input': 0.0, 'output': 0.0})
    
    def _get_context_window(self, model_id: str) -> Optional[int]:
        """Get context window size for a model."""
        context_windows = {
            'gpt-4': 8192,
            'gpt-4-32k': 32768,
            'gpt-4-turbo': 128000,
            'gpt-4-vision-preview': 128000,
            'gpt-3.5-turbo': 4096,
            'gpt-3.5-turbo-16k': 16384,
        }
        
        return context_windows.get(model_id)
    
    def _get_max_output_tokens(self, model_id: str) -> Optional[int]:
        """Get max output tokens for a model."""
        # Most models can output up to 1/4 of their context window
        context_window = self._get_context_window(model_id)
        if context_window:
            return min(4096, context_window // 4)
        return None
    
    def _calculate_cost(self, usage: TokenUsage, model: str) -> float:
        """Calculate cost based on usage."""
        pricing = self._get_model_pricing(model)
        
        input_cost = (usage.prompt_tokens / 1000) * pricing.get('input', 0.0)
        output_cost = (usage.completion_tokens / 1000) * pricing.get('output', 0.0)
        
        return input_cost + output_cost
    
    def _calculate_image_cost(self, model: str, size: str, quality: str, n: int) -> float:
        """Calculate cost for image generation."""
        # DALL-E pricing
        if model == 'dall-e-3':
            if size == '1024x1024':
                cost_per_image = 0.04 if quality == 'standard' else 0.08
            elif size == '1792x1024' or size == '1024x1792':
                cost_per_image = 0.08 if quality == 'standard' else 0.12
            else:
                cost_per_image = 0.04
        elif model == 'dall-e-2':
            if size == '1024x1024':
                cost_per_image = 0.02
            elif size == '512x512':
                cost_per_image = 0.018
            elif size == '256x256':
                cost_per_image = 0.016
            else:
                cost_per_image = 0.02
        else:
            cost_per_image = 0.02
        
        return cost_per_image * n
    
    def _handle_error(self, error: Exception):
        """Handle OpenAI-specific errors."""
        error_str = str(error).lower()
        
        if hasattr(error, 'status_code'):
            if error.status_code == 401:
                raise AuthenticationError(f"OpenAI authentication failed: {error}", self.name)
            elif error.status_code == 404:
                raise ModelNotFoundError(f"OpenAI model not found: {error}", self.name, "unknown")
            elif error.status_code == 429:
                retry_after = getattr(error, 'retry_after', None)
                raise RateLimitError(f"OpenAI rate limit exceeded: {error}", self.name, retry_after)
        
        if 'rate limit' in error_str or 'too many requests' in error_str:
            raise RateLimitError(f"OpenAI rate limit: {error}", self.name)
        elif 'unauthorized' in error_str or 'invalid api key' in error_str:
            raise AuthenticationError(f"OpenAI authentication error: {error}", self.name)
        elif 'not found' in error_str:
            raise ModelNotFoundError(f"OpenAI model not found: {error}", self.name, "unknown")
        else:
            raise ProviderError(f"OpenAI error: {error}", self.name)