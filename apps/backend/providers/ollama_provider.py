"""
Ollama provider implementation for local models.
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import time
import logging
import json

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

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


class OllamaProvider(BaseProvider):
    """Ollama provider implementation for local models."""
    
    def __init__(self, credentials: ProviderCredentials):
        if not HTTPX_AVAILABLE:
            raise ProviderError("httpx library not installed. Run: pip install httpx", "ollama")
        
        super().__init__(credentials)
        self._client: Optional[httpx.AsyncClient] = None
        self.base_url = credentials.endpoint or "http://localhost:11434"
    
    @property
    def name(self) -> str:
        return "ollama"
    
    @property
    def display_name(self) -> str:
        return "Ollama (Local)"
    
    async def initialize(self) -> None:
        """Initialize Ollama client."""
        try:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=60.0
            )
            
            # Test connection
            response = await self._client.get("/api/version")
            response.raise_for_status()
            
            logger.info("Ollama provider initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Ollama provider: {e}")
            raise AuthenticationError(f"Ollama initialization failed: {e}", self.name)
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get available Ollama models."""
        try:
            response = await self._client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model_data in data.get("models", []):
                model_id = model_data.get("name", "")
                
                # Determine capabilities based on model name
                capabilities = [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT]
                if "code" in model_id.lower():
                    capabilities.append(ModelCapability.CODE_GENERATION)
                if "vision" in model_id.lower() or "llava" in model_id.lower():
                    capabilities.append(ModelCapability.VISION)
                
                model_info = ModelInfo(
                    id=model_id,
                    name=model_data.get("name", model_id),
                    provider=ProviderType.OLLAMA,
                    capabilities=capabilities,
                    context_window=self._estimate_context_window(model_id),
                    max_output_tokens=4096,  # Default for most models
                    input_cost_per_1k=0.0,  # Local models are free
                    output_cost_per_1k=0.0,
                    supports_streaming=True,
                    supports_functions=False,
                    supports_vision="vision" in model_id.lower() or "llava" in model_id.lower(),
                    is_available=True
                )
                models.append(model_info)
            
            return models
            
        except Exception as e:
            self._handle_error(e)
    
    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Ollama."""
        start_time = time.time()
        
        try:
            # Convert our format to Ollama format
            ollama_request = self._convert_to_ollama_request(request)
            
            if request.stream:
                # For streaming, collect all chunks
                chunks = []
                async for chunk in self.stream_text(request):
                    chunks.append(chunk.delta)
                
                content = ''.join(chunks)
                usage = TokenUsage()  # Estimate this
                
            else:
                # Standard completion
                if request.messages:
                    # Use chat endpoint
                    response = await self._client.post("/api/chat", json=ollama_request)
                    response.raise_for_status()
                    data = response.json()
                    
                    content = data.get("message", {}).get("content", "")
                else:
                    # Use generate endpoint
                    response = await self._client.post("/api/generate", json=ollama_request)
                    response.raise_for_status()
                    data = response.json()
                    
                    content = data.get("response", "")
                
                # Extract usage information
                prompt_eval_count = data.get("prompt_eval_count", 0)
                eval_count = data.get("eval_count", 0)
                
                usage = TokenUsage(
                    prompt_tokens=prompt_eval_count,
                    completion_tokens=eval_count,
                    total_tokens=prompt_eval_count + eval_count
                )
                
                finish_reason = "stop"
            
            response_time = time.time() - start_time
            
            # Local models have no cost
            cost = 0.0
            
            return GenerationResponse(
                content=content,
                model=request.model,
                provider=ProviderType.OLLAMA,
                finish_reason=finish_reason,
                usage=usage,
                function_call=None,
                tool_calls=None,
                response_time=response_time,
                cost=cost,
                raw_response=data if 'data' in locals() else None
            )
            
        except Exception as e:
            self._handle_error(e)
    
    async def stream_text(self, request: GenerationRequest) -> AsyncGenerator[StreamChunk, None]:
        """Stream text generation using Ollama."""
        try:
            ollama_request = self._convert_to_ollama_request(request)
            ollama_request['stream'] = True
            
            endpoint = "/api/chat" if request.messages else "/api/generate"
            
            async with self._client.stream("POST", endpoint, json=ollama_request) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line:
                        try:
                            chunk_data = json.loads(line)
                            
                            if request.messages:
                                # Chat format
                                delta = chunk_data.get("message", {}).get("content", "")
                            else:
                                # Generate format
                                delta = chunk_data.get("response", "")
                            
                            done = chunk_data.get("done", False)
                            
                            if delta:
                                yield StreamChunk(
                                    delta=delta,
                                    finish_reason=None,
                                    metadata={'chunk': chunk_data}
                                )
                            
                            if done:
                                yield StreamChunk(
                                    delta="",
                                    finish_reason="stop",
                                    metadata={'chunk': chunk_data}
                                )
                                break
                                
                        except json.JSONDecodeError:
                            continue
                    
        except Exception as e:
            self._handle_error(e)
    
    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using Ollama."""
        start_time = time.time()
        
        try:
            # Handle both single string and list of strings
            texts = request.input if isinstance(request.input, list) else [request.input]
            
            embeddings = []
            total_tokens = 0
            
            for text in texts:
                response = await self._client.post("/api/embeddings", json={
                    "model": request.model,
                    "prompt": text
                })
                response.raise_for_status()
                data = response.json()
                
                embeddings.append(data.get("embedding", []))
                # Estimate tokens
                total_tokens += len(text.split())
            
            usage = TokenUsage(
                prompt_tokens=total_tokens,
                total_tokens=total_tokens
            )
            
            response_time = time.time() - start_time
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=request.model,
                provider=ProviderType.OLLAMA,
                usage=usage,
                response_time=response_time,
                cost=0.0  # Local models are free
            )
            
        except Exception as e:
            self._handle_error(e)
    
    def _convert_to_ollama_request(self, request: GenerationRequest) -> Dict[str, Any]:
        """Convert our request format to Ollama format."""
        ollama_request = {
            'model': request.model,
        }
        
        if request.messages:
            # Chat format
            messages = []
            
            for msg in request.messages:
                messages.append({
                    'role': msg.role.value,
                    'content': msg.content
                })
            
            ollama_request['messages'] = messages
        else:
            # Generate format
            ollama_request['prompt'] = request.prompt
        
        # Options
        options = {}
        if request.max_tokens:
            options['num_predict'] = request.max_tokens
        if request.temperature is not None:
            options['temperature'] = request.temperature
        if request.top_p is not None:
            options['top_p'] = request.top_p
        if request.stop:
            options['stop'] = request.stop if isinstance(request.stop, list) else [request.stop]
        
        if options:
            ollama_request['options'] = options
        
        return ollama_request
    
    def _estimate_context_window(self, model_id: str) -> int:
        """Estimate context window based on model name."""
        model_lower = model_id.lower()
        
        # Common context windows for different model families
        if "llama" in model_lower:
            if "70b" in model_lower or "65b" in model_lower:
                return 4096
            elif "13b" in model_lower:
                return 4096
            elif "7b" in model_lower:
                return 4096
            else:
                return 2048
        elif "codellama" in model_lower:
            return 16384
        elif "mistral" in model_lower:
            return 8192
        elif "phi" in model_lower:
            return 2048
        else:
            return 4096  # Default
    
    def _handle_error(self, error: Exception):
        """Handle Ollama-specific errors."""
        error_str = str(error).lower()
        
        if hasattr(error, 'status_code'):
            if error.status_code == 404:
                if "model" in error_str:
                    raise ModelNotFoundError(f"Ollama model not found: {error}", self.name, "unknown")
                else:
                    raise ProviderError(f"Ollama endpoint not found: {error}", self.name)
            elif error.status_code >= 500:
                raise ProviderError(f"Ollama server error: {error}", self.name)
        
        if "connection" in error_str or "timeout" in error_str:
            raise ProviderError(f"Ollama connection error: {error}", self.name)
        elif "not found" in error_str:
            raise ModelNotFoundError(f"Ollama model not found: {error}", self.name, "unknown")
        else:
            raise ProviderError(f"Ollama error: {error}", self.name)