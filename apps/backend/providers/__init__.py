"""
AI Provider Integration System

This module provides a unified interface for interacting with various AI providers
including OpenAI, Anthropic, Google AI, and others. It abstracts provider-specific
implementations while maintaining access to unique features.
"""

from .base import BaseProvider, ProviderError, ProviderResponse
from .registry import ProviderRegistry, get_provider, list_providers
from .cost_tracker import CostTracker, UsageMetrics
from .types import (
    ProviderType,
    ModelCapability,
    GenerationRequest,
    GenerationResponse,
    ProviderCredentials,
    RateLimitInfo,
    Message,
    MessageRole
)

__all__ = [
    'BaseProvider',
    'ProviderError', 
    'ProviderResponse',
    'ProviderRegistry',
    'get_provider',
    'list_providers',
    'CostTracker',
    'UsageMetrics',
    'ProviderType',
    'ModelCapability',
    'GenerationRequest',
    'GenerationResponse',
    'ProviderCredentials',
    'RateLimitInfo',
    'Message',
    'MessageRole'
]