"""
Cohere provider implementation.
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import time
import logging

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False

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


class CohereProvider(BaseProvider):
    """Cohere provider implementation."""
    
    def __init__(self, credentials: ProviderCredentials):
        if not COHERE_AVAILABLE:
            raise ProviderError("Cohere library not installed. Run: pip install cohere", "cohere")
        
        super().__init__(credentials)
        self._client: Optional[cohere.AsyncClient] = None
    
    @property
    def name(self) -> str:
        return "cohere"
    
    @property
    def display_name(self) -> str:
        return "Cohere"
    
    async def initialize(self) -> None:
        """Initialize Cohere client."""
        try:
            self._client = cohere.AsyncClient(
                api_key=self.credentials.api_key,
                timeout=30.0
            )
            
            # Test connection
            await self._client.check_api_key()
            logger.info("Cohere provider initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Cohere provider: {e}")
            raise AuthenticationError(f"Cohere initialization failed: {e}", self.name)
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get available Cohere models."""
        try:
            # Cohere models (as of 2024)
            models_data = [
                {
                    "id": "command-r-plus",
                    "name": "Command R+",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
                    "context_window": 128000,
                    "max_output_tokens": 4000,
                    "input_cost_per_1k": 0.003,
                    "output_cost_per_1k": 0.015
                },
                {
                    "id": "command-r",
                    "name": "Command R",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING],
                    "context_window": 128000,
                    "max_output_tokens": 4000,
                    "input_cost_per_1k": 0.0005,
                    "output_cost_per_1k": 0.0015
                },
                {
                    "id": "command",
                    "name": "Command",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT],
                    "context_window": 4096,
                    "max_output_tokens": 4000,
                    "input_cost_per_1k": 0.0015,
                    "output_cost_per_1k": 0.002
                },
                {
                    "id": "command-light",
                    "name": "Command Light",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT],
                    "context_window": 4096,
                    "max_output_tokens": 4000,
                    "input_cost_per_1k": 0.0003,
                    "output_cost_per_1k": 0.0006
                },
                {
                    "id": "embed-english-v3.0",
                    "name": "Embed English v3.0",
                    "capabilities": [ModelCapability.EMBEDDINGS],
                    "context_window": 512,
                    "max_output_tokens": None,
                    "input_cost_per_1k": 0.0001,
                    "output_cost_per_1k": 0.0
                },
                {
                    "id": "embed-multilingual-v3.0",
                    "name": "Embed Multilingual v3.0",
                    "capabilities": [ModelCapability.EMBEDDINGS],
                    "context_window": 512,
                    "max_output_tokens": None,
                    "input_cost_per_1k": 0.0001,
                    "output_cost_per_1k": 0.0
                }
            ]
            
            models = []
            for model_data in models_data:
                model_info = ModelInfo(
                    id=model_data["id"],
                    name=model_data["name"],
                    provider=ProviderType.COHERE,
                    capabilities=model_data["capabilities"],
                    context_window=model_data["context_window"],
                    max_output_tokens=model_data["max_output_tokens"],
                    input_cost_per_1k=model_data["input_cost_per_1k"],
                    output_cost_per_1k=model_data["output_cost_per_1k"],
                    supports_streaming=True,
                    supports_functions=False,
                    supports_vision=False,
                    is_available=True
                )
                models.append(model_info)
            
            return models
            
        except Exception as e:
            self._handle_error(e)
    
    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Cohere."""
        start_time = time.time()
        
        try:
            # Convert our format to Cohere format
            cohere_request = self._convert_to_cohere_request(request)
            
            if request.stream:
                # For streaming, collect all chunks
                chunks = []
                async for chunk in self.stream_text(request):
                    chunks.append(chunk.delta)
                
                content = ''.join(chunks)
                usage = TokenUsage()  # We'll estimate this
                
            else:
                # Standard completion
                if request.messages:
                    # Use chat endpoint
                    response = await self._client.chat(**cohere_request)
                    content = response.text
                    
                    # Extract usage information
                    usage = TokenUsage(
                        prompt_tokens=response.meta.tokens.input_tokens if response.meta and response.meta.tokens else 0,
                        completion_tokens=response.meta.tokens.output_tokens if response.meta and response.meta.tokens else 0,
                        total_tokens=response.meta.tokens.input_tokens + response.meta.tokens.output_tokens if response.meta and response.meta.tokens else 0
                    )
                else:
                    # Use generate endpoint
                    response = await self._client.generate(**cohere_request)
                    content = response.generations[0].text if response.generations else ""
                    
                    # Estimate usage
                    usage = TokenUsage(
                        prompt_tokens=len(request.prompt.split()) if request.prompt else 0,
                        completion_tokens=len(content.split()),
                        total_tokens=len(request.prompt.split()) + len(content.split()) if request.prompt else len(content.split())
                    )
                
                finish_reason = "stop"
            
            response_time = time.time() - start_time
            
            # Calculate cost
            cost = self._calculate_cost(usage, request.model)
            
            return GenerationResponse(
                content=content,
                model=request.model,
                provider=ProviderType.COHERE,
                finish_reason=finish_reason,
                usage=usage,
                function_call=None,
                tool_calls=None,
                response_time=response_time,
                cost=cost,
                raw_response=response.__dict__ if hasattr(response, '__dict__') else None
            )
            
        except Exception as e:
            self._handle_error(e)
    
    async def stream_text(self, request: GenerationRequest) -> AsyncGenerator[StreamChunk, None]:
        """Stream text generation using Cohere."""
        try:
            cohere_request = self._convert_to_cohere_request(request)
            cohere_request['stream'] = True
            
            if request.messages:
                # Use chat endpoint
                stream = self._client.chat_stream(**cohere_request)
            else:
                # Use generate endpoint
                stream = self._client.generate(**cohere_request)
            
            async for chunk in stream:
                if hasattr(chunk, 'text') and chunk.text:
                    yield StreamChunk(
                        delta=chunk.text,
                        finish_reason=None,
                        metadata={'chunk': chunk.__dict__ if hasattr(chunk, '__dict__') else None}
                    )
                elif hasattr(chunk, 'finish_reason'):
                    yield StreamChunk(
                        delta="",
                        finish_reason=chunk.finish_reason,
                        metadata={}
                    )
                    
        except Exception as e:
            self._handle_error(e)
    
    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using Cohere."""
        start_time = time.time()
        
        try:
            # Handle both single string and list of strings
            texts = request.input if isinstance(request.input, list) else [request.input]
            
            response = await self._client.embed(
                texts=texts,
                model=request.model,
                input_type="search_document"
            )
            
            embeddings = response.embeddings
            
            # Estimate tokens
            total_tokens = sum(len(text.split()) for text in texts)
            usage = TokenUsage(
                prompt_tokens=total_tokens,
                total_tokens=total_tokens
            )
            
            response_time = time.time() - start_time
            cost = self._calculate_cost(usage, request.model)
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=request.model,
                provider=ProviderType.COHERE,
                usage=usage,
                response_time=response_time,
                cost=cost
            )
            
        except Exception as e:
            self._handle_error(e)
    
    def _convert_to_cohere_request(self, request: GenerationRequest) -> Dict[str, Any]:
        """Convert our request format to Cohere format."""
        cohere_request = {
            'model': request.model,
        }
        
        if request.messages:
            # Chat format
            message_history = []
            
            for msg in request.messages:
                if msg.role == MessageRole.USER:
                    message_history.append({
                        'role': 'USER',
                        'message': msg.content
                    })
                elif msg.role == MessageRole.ASSISTANT:
                    message_history.append({
                        'role': 'CHATBOT',
                        'message': msg.content
                    })
                # System messages are handled differently in Cohere
            
            cohere_request['chat_history'] = message_history[:-1] if message_history else []
            cohere_request['message'] = message_history[-1]['message'] if message_history else ""
        else:
            # Generate format
            cohere_request['prompt'] = request.prompt
        
        # Optional parameters
        if request.max_tokens:
            cohere_request['max_tokens'] = request.max_tokens
        if request.temperature is not None:
            cohere_request['temperature'] = request.temperature
        if request.top_p is not None:
            cohere_request['p'] = request.top_p
        if request.stop:
            cohere_request['stop_sequences'] = request.stop if isinstance(request.stop, list) else [request.stop]
        
        return cohere_request
    
    def _calculate_cost(self, usage: TokenUsage, model: str) -> float:
        """Calculate cost based on usage."""
        # Cohere pricing (per 1K tokens)
        pricing_map = {
            'command-r-plus': {'input': 0.003, 'output': 0.015},
            'command-r': {'input': 0.0005, 'output': 0.0015},
            'command': {'input': 0.0015, 'output': 0.002},
            'command-light': {'input': 0.0003, 'output': 0.0006},
            'embed-english-v3.0': {'input': 0.0001, 'output': 0.0},
            'embed-multilingual-v3.0': {'input': 0.0001, 'output': 0.0},
        }
        
        pricing = pricing_map.get(model, {'input': 0.0015, 'output': 0.002})
        
        input_cost = (usage.prompt_tokens / 1000) * pricing['input']
        output_cost = (usage.completion_tokens / 1000) * pricing['output']
        
        return input_cost + output_cost
    
    def _handle_error(self, error: Exception):
        """Handle Cohere-specific errors."""
        error_str = str(error).lower()
        
        if hasattr(error, 'status_code'):
            if error.status_code == 401:
                raise AuthenticationError(f"Cohere authentication failed: {error}", self.name)
            elif error.status_code == 404:
                raise ModelNotFoundError(f"Cohere model not found: {error}", self.name, "unknown")
            elif error.status_code == 429:
                retry_after = getattr(error, 'retry_after', None)
                raise RateLimitError(f"Cohere rate limit exceeded: {error}", self.name, retry_after)
        
        if 'rate limit' in error_str or 'too many requests' in error_str:
            raise RateLimitError(f"Cohere rate limit: {error}", self.name)
        elif 'unauthorized' in error_str or 'invalid api key' in error_str:
            raise AuthenticationError(f"Cohere authentication error: {error}", self.name)
        elif 'not found' in error_str:
            raise ModelNotFoundError(f"Cohere model not found: {error}", self.name, "unknown")
        else:
            raise ProviderError(f"Cohere error: {error}", self.name)