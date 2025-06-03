"""
Type definitions for the provider system.
"""

from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel
from datetime import datetime


class ProviderType(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    OLLAMA = "ollama"
    LOCAL = "local"


class ModelCapability(str, Enum):
    """AI model capabilities."""
    TEXT_GENERATION = "text_generation"
    TEXT_COMPLETION = "text_completion"
    CHAT = "chat"
    IMAGE_GENERATION = "image_generation"
    IMAGE_ANALYSIS = "image_analysis"
    SPEECH_TO_TEXT = "speech_to_text"
    TEXT_TO_SPEECH = "text_to_speech"
    EMBEDDINGS = "embeddings"
    FUNCTION_CALLING = "function_calling"
    VISION = "vision"
    MULTIMODAL = "multimodal"
    CODE_GENERATION = "code_generation"
    REASONING = "reasoning"


class MessageRole(str, Enum):
    """Message roles in conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"
    TOOL = "tool"


class ProviderCredentials(BaseModel):
    """Provider authentication credentials."""
    provider_type: ProviderType
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    organization_id: Optional[str] = None
    project_id: Optional[str] = None
    region: Optional[str] = None
    endpoint: Optional[str] = None
    additional_headers: Optional[Dict[str, str]] = None
    
    class Config:
        use_enum_values = True


class Message(BaseModel):
    """A message in a conversation."""
    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    class Config:
        use_enum_values = True


class GenerationRequest(BaseModel):
    """Request for text generation."""
    messages: Optional[List[Message]] = None
    prompt: Optional[str] = None
    model: str
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    top_p: Optional[float] = None
    frequency_penalty: Optional[float] = None
    presence_penalty: Optional[float] = None
    stop: Optional[Union[str, List[str]]] = None
    stream: bool = False
    response_format: Optional[str] = "text"
    functions: Optional[List[Dict[str, Any]]] = None
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[Union[str, Dict[str, Any]]] = None
    
    # Provider-specific options
    extra_params: Optional[Dict[str, Any]] = None


class TokenUsage(BaseModel):
    """Token usage information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class GenerationResponse(BaseModel):
    """Response from text generation."""
    content: str
    model: str
    provider: ProviderType
    finish_reason: Optional[str] = None
    usage: Optional[TokenUsage] = None
    function_call: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    response_time: float
    cost: float = 0.0
    
    # Provider-specific metadata
    raw_response: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class ModelInfo(BaseModel):
    """Information about an AI model."""
    id: str
    name: str
    provider: ProviderType
    capabilities: List[ModelCapability]
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    
    # Pricing information (per 1K tokens)
    input_cost_per_1k: Optional[float] = None
    output_cost_per_1k: Optional[float] = None
    
    # Model specifications
    parameter_count: Optional[str] = None
    training_data_cutoff: Optional[str] = None
    supports_streaming: bool = True
    supports_functions: bool = False
    supports_vision: bool = False
    
    # Availability
    is_available: bool = True
    deprecation_date: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class RateLimitInfo(BaseModel):
    """Rate limiting information."""
    requests_per_minute: Optional[int] = None
    tokens_per_minute: Optional[int] = None
    requests_remaining: Optional[int] = None
    tokens_remaining: Optional[int] = None
    reset_time: Optional[datetime] = None
    retry_after_seconds: Optional[int] = None


class ProviderStatus(BaseModel):
    """Provider operational status."""
    provider: ProviderType
    is_available: bool = True
    last_check: datetime
    response_time: Optional[float] = None
    error_rate: float = 0.0
    rate_limit_info: Optional[RateLimitInfo] = None
    
    class Config:
        use_enum_values = True


class UsageStatistics(BaseModel):
    """Usage statistics for a provider."""
    provider: ProviderType
    requests_count: int = 0
    tokens_consumed: int = 0
    total_cost: float = 0.0
    error_count: int = 0
    average_response_time: float = 0.0
    last_used: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class StreamChunk(BaseModel):
    """Streaming response chunk."""
    delta: str
    finish_reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class EmbeddingRequest(BaseModel):
    """Request for text embeddings."""
    input: Union[str, List[str]]
    model: str
    encoding_format: str = "float"
    dimensions: Optional[int] = None


class EmbeddingResponse(BaseModel):
    """Response from embedding generation."""
    embeddings: List[List[float]]
    model: str
    provider: ProviderType
    usage: Optional[TokenUsage] = None
    response_time: float
    cost: float = 0.0
    
    class Config:
        use_enum_values = True


class ImageGenerationRequest(BaseModel):
    """Request for image generation."""
    prompt: str
    model: str
    size: str = "1024x1024"
    quality: str = "standard"
    style: Optional[str] = None
    n: int = 1
    response_format: str = "url"


class ImageGenerationResponse(BaseModel):
    """Response from image generation."""
    images: List[Dict[str, Any]]  # Contains URLs or base64 data
    model: str
    provider: ProviderType
    response_time: float
    cost: float = 0.0
    
    class Config:
        use_enum_values = True