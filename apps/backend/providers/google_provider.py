"""
Google AI (Gemini) provider implementation.
"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator
import time
import logging

try:
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False

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


class GoogleProvider(BaseProvider):
    """Google AI (Gemini) provider implementation."""
    
    def __init__(self, credentials: ProviderCredentials):
        if not GOOGLE_AI_AVAILABLE:
            raise ProviderError("Google AI library not installed. Run: pip install google-generativeai", "google")
        
        super().__init__(credentials)
        self._configured = False
    
    @property
    def name(self) -> str:
        return "google"
    
    @property
    def display_name(self) -> str:
        return "Google AI"
    
    async def initialize(self) -> None:
        """Initialize Google AI client."""
        try:
            # Configure the API key
            genai.configure(api_key=self.credentials.api_key)
            self._configured = True
            
            # Test connection by listing models
            models = genai.list_models()
            list(models)  # Force evaluation to test connection
            
            logger.info("Google AI provider initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google AI provider: {e}")
            raise AuthenticationError(f"Google AI initialization failed: {e}", self.name)
    
    async def get_available_models(self) -> List[ModelInfo]:
        """Get available Google AI models."""
        try:
            # Google AI models (as of 2024)
            models_data = [
                {
                    "id": "gemini-1.5-pro-latest",
                    "name": "Gemini 1.5 Pro",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.VISION, ModelCapability.MULTIMODAL],
                    "context_window": 2000000,  # 2M context window
                    "max_output_tokens": 8192,
                    "input_cost_per_1k": 0.00125,
                    "output_cost_per_1k": 0.00375
                },
                {
                    "id": "gemini-1.5-flash-latest",
                    "name": "Gemini 1.5 Flash",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE_GENERATION, ModelCapability.VISION, ModelCapability.MULTIMODAL],
                    "context_window": 1000000,  # 1M context window
                    "max_output_tokens": 8192,
                    "input_cost_per_1k": 0.000075,
                    "output_cost_per_1k": 0.0003
                },
                {
                    "id": "gemini-pro",
                    "name": "Gemini Pro",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.CODE_GENERATION],
                    "context_window": 32768,
                    "max_output_tokens": 8192,
                    "input_cost_per_1k": 0.0005,
                    "output_cost_per_1k": 0.0015
                },
                {
                    "id": "gemini-pro-vision",
                    "name": "Gemini Pro Vision",
                    "capabilities": [ModelCapability.TEXT_GENERATION, ModelCapability.CHAT, ModelCapability.REASONING, ModelCapability.VISION, ModelCapability.MULTIMODAL],
                    "context_window": 16384,
                    "max_output_tokens": 2048,
                    "input_cost_per_1k": 0.00025,
                    "output_cost_per_1k": 0.0005
                },
                {
                    "id": "text-embedding-004",
                    "name": "Text Embedding 004",
                    "capabilities": [ModelCapability.EMBEDDINGS],
                    "context_window": 2048,
                    "max_output_tokens": None,
                    "input_cost_per_1k": 0.00001,
                    "output_cost_per_1k": 0.0
                }
            ]
            
            models = []
            for model_data in models_data:
                model_info = ModelInfo(
                    id=model_data["id"],
                    name=model_data["name"],
                    provider=ProviderType.GOOGLE,
                    capabilities=model_data["capabilities"],
                    context_window=model_data["context_window"],
                    max_output_tokens=model_data["max_output_tokens"],
                    input_cost_per_1k=model_data["input_cost_per_1k"],
                    output_cost_per_1k=model_data["output_cost_per_1k"],
                    supports_streaming=True,
                    supports_functions=False,
                    supports_vision=ModelCapability.VISION in model_data["capabilities"],
                    is_available=True
                )
                models.append(model_info)
            
            return models
            
        except Exception as e:
            self._handle_error(e)
    
    async def generate_text(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Google AI Gemini."""
        start_time = time.time()
        
        try:
            # Get the model
            model = genai.GenerativeModel(request.model)
            
            # Convert our format to Google format
            prompt = self._convert_to_google_prompt(request)
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens or 8192,
                temperature=request.temperature if request.temperature is not None else 0.7,
                top_p=request.top_p if request.top_p is not None else 1.0,
                stop_sequences=request.stop if request.stop else None
            )
            
            # Safety settings (less restrictive for development)
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            }
            
            if request.stream:
                # For streaming, collect all chunks
                chunks = []
                async for chunk in self.stream_text(request):
                    chunks.append(chunk.delta)
                
                content = ''.join(chunks)
                usage = TokenUsage()  # We'll estimate this
                finish_reason = "stop"
                
            else:
                # Standard completion
                response = model.generate_content(
                    prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
                
                # Extract content
                content = response.text if response.text else ""
                
                # Extract usage information
                usage_metadata = response.usage_metadata if hasattr(response, 'usage_metadata') else None
                usage = TokenUsage(
                    prompt_tokens=usage_metadata.prompt_token_count if usage_metadata else 0,
                    completion_tokens=usage_metadata.candidates_token_count if usage_metadata else 0,
                    total_tokens=usage_metadata.total_token_count if usage_metadata else 0
                )
                
                # Determine finish reason
                finish_reason = "stop"
                if response.candidates and response.candidates[0].finish_reason:
                    finish_reason = str(response.candidates[0].finish_reason).lower()
            
            response_time = time.time() - start_time
            
            # Calculate cost
            cost = self._calculate_cost(usage, request.model)
            
            return GenerationResponse(
                content=content,
                model=request.model,
                provider=ProviderType.GOOGLE,
                finish_reason=finish_reason,
                usage=usage,
                function_call=None,
                tool_calls=None,
                response_time=response_time,
                cost=cost,
                raw_response=response._result if hasattr(response, '_result') else None
            )
            
        except Exception as e:
            self._handle_error(e)
    
    async def stream_text(self, request: GenerationRequest) -> AsyncGenerator[StreamChunk, None]:
        """Stream text generation using Google AI Gemini."""
        try:
            # Get the model
            model = genai.GenerativeModel(request.model)
            
            # Convert our format to Google format
            prompt = self._convert_to_google_prompt(request)
            
            # Configure generation parameters
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens or 8192,
                temperature=request.temperature if request.temperature is not None else 0.7,
                top_p=request.top_p if request.top_p is not None else 1.0,
                stop_sequences=request.stop if request.stop else None
            )
            
            # Generate streaming response
            response = model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield StreamChunk(
                        delta=chunk.text,
                        finish_reason=None,
                        metadata={'chunk': str(chunk)}
                    )
            
            # Send final chunk with finish reason
            yield StreamChunk(
                delta="",
                finish_reason="stop",
                metadata={}
            )
                    
        except Exception as e:
            self._handle_error(e)
    
    async def generate_embeddings(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Generate embeddings using Google AI."""
        start_time = time.time()
        
        try:
            # Use text-embedding model
            model_name = request.model if 'embedding' in request.model else 'text-embedding-004'
            
            # Handle both single string and list of strings
            texts = request.input if isinstance(request.input, list) else [request.input]
            
            embeddings = []
            total_tokens = 0
            
            for text in texts:
                result = genai.embed_content(
                    model=f"models/{model_name}",
                    content=text,
                    task_type="retrieval_document"
                )
                embeddings.append(result['embedding'])
                # Estimate tokens (Google AI doesn't provide exact token counts for embeddings)
                total_tokens += len(text.split())
            
            usage = TokenUsage(
                prompt_tokens=total_tokens,
                total_tokens=total_tokens
            )
            
            response_time = time.time() - start_time
            cost = self._calculate_cost(usage, model_name)
            
            return EmbeddingResponse(
                embeddings=embeddings,
                model=model_name,
                provider=ProviderType.GOOGLE,
                usage=usage,
                response_time=response_time,
                cost=cost
            )
            
        except Exception as e:
            self._handle_error(e)
    
    def _convert_to_google_prompt(self, request: GenerationRequest) -> str:
        """Convert our request format to Google format."""
        if request.messages:
            # Convert messages to a single prompt
            prompt_parts = []
            
            for msg in request.messages:
                if msg.role == MessageRole.SYSTEM:
                    prompt_parts.append(f"System: {msg.content}")
                elif msg.role == MessageRole.USER:
                    prompt_parts.append(f"Human: {msg.content}")
                elif msg.role == MessageRole.ASSISTANT:
                    prompt_parts.append(f"Assistant: {msg.content}")
            
            return "\n\n".join(prompt_parts)
        else:
            return request.prompt or ""
    
    def _calculate_cost(self, usage: TokenUsage, model: str) -> float:
        """Calculate cost based on usage."""
        # Google AI pricing (per 1K tokens)
        pricing_map = {
            'gemini-1.5-pro-latest': {'input': 0.00125, 'output': 0.00375},
            'gemini-1.5-flash-latest': {'input': 0.000075, 'output': 0.0003},
            'gemini-pro': {'input': 0.0005, 'output': 0.0015},
            'gemini-pro-vision': {'input': 0.00025, 'output': 0.0005},
            'text-embedding-004': {'input': 0.00001, 'output': 0.0},
        }
        
        pricing = pricing_map.get(model, {'input': 0.0005, 'output': 0.0015})
        
        input_cost = (usage.prompt_tokens / 1000) * pricing['input']
        output_cost = (usage.completion_tokens / 1000) * pricing['output']
        
        return input_cost + output_cost
    
    def _handle_error(self, error: Exception):
        """Handle Google AI-specific errors."""
        error_str = str(error).lower()
        
        if hasattr(error, 'status_code'):
            if error.status_code == 401:
                raise AuthenticationError(f"Google AI authentication failed: {error}", self.name)
            elif error.status_code == 404:
                raise ModelNotFoundError(f"Google AI model not found: {error}", self.name, "unknown")
            elif error.status_code == 429:
                retry_after = getattr(error, 'retry_after', None)
                raise RateLimitError(f"Google AI rate limit exceeded: {error}", self.name, retry_after)
        
        if 'quota' in error_str or 'rate limit' in error_str or 'too many requests' in error_str:
            raise RateLimitError(f"Google AI rate limit: {error}", self.name)
        elif 'unauthorized' in error_str or 'invalid api key' in error_str or 'authentication' in error_str:
            raise AuthenticationError(f"Google AI authentication error: {error}", self.name)
        elif 'not found' in error_str:
            raise ModelNotFoundError(f"Google AI model not found: {error}", self.name, "unknown")
        else:
            raise ProviderError(f"Google AI error: {error}", self.name)