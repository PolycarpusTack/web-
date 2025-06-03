"""
Provider registry for managing and accessing AI providers.
"""

from typing import Dict, List, Optional, Type, Union
import logging
from datetime import datetime
from contextlib import asynccontextmanager

from .base import BaseProvider, ProviderError
from .types import ProviderType, ProviderCredentials, ModelInfo, ProviderStatus
from .cost_tracker_db import get_cost_tracker

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Registry for managing AI providers."""
    
    def __init__(self):
        self._providers: Dict[str, Type[BaseProvider]] = {}
        self._instances: Dict[str, BaseProvider] = {}
        self._cost_tracker = get_cost_tracker()
        
    def register_provider(self, provider_class: Type[BaseProvider], provider_type: ProviderType):
        """Register a provider class."""
        key = f"{provider_type.value}"
        self._providers[key] = provider_class
        logger.info(f"Registered provider: {provider_type.value}")
    
    def unregister_provider(self, provider_type: ProviderType):
        """Unregister a provider."""
        key = f"{provider_type.value}"
        if key in self._providers:
            del self._providers[key]
        if key in self._instances:
            del self._instances[key]
        logger.info(f"Unregistered provider: {provider_type.value}")
    
    async def get_provider(self, provider_type: ProviderType, credentials: ProviderCredentials) -> BaseProvider:
        """Get a provider instance."""
        key = f"{provider_type.value}"
        
        if key not in self._providers:
            raise ProviderError(f"Provider {provider_type.value} not registered", "registry")
        
        # Create new instance with credentials
        provider_class = self._providers[key]
        instance = provider_class(credentials)
        
        # Initialize the provider
        await instance.initialize()
        
        return instance
    
    @asynccontextmanager
    async def get_provider_context(self, provider_type: ProviderType, credentials: ProviderCredentials):
        """Get a provider instance as a context manager."""
        provider = await self.get_provider(provider_type, credentials)
        try:
            yield provider
        finally:
            await provider.close()
    
    async def get_cached_provider(self, provider_type: ProviderType, credentials: ProviderCredentials) -> BaseProvider:
        """Get a cached provider instance (reuse if credentials match)."""
        key = f"{provider_type.value}_{hash(str(credentials))}"
        
        if key not in self._instances:
            self._instances[key] = await self.get_provider(provider_type, credentials)
        
        return self._instances[key]
    
    def list_registered_providers(self) -> List[str]:
        """List all registered provider types."""
        return list(self._providers.keys())
    
    async def get_all_models(self, credentials_map: Dict[ProviderType, ProviderCredentials]) -> Dict[str, List[ModelInfo]]:
        """Get available models from all providers."""
        results = {}
        
        for provider_type, credentials in credentials_map.items():
            try:
                async with self.get_provider_context(provider_type, credentials) as provider:
                    models = await provider.get_available_models()
                    results[provider_type.value] = models
            except Exception as e:
                logger.error(f"Failed to get models from {provider_type.value}: {e}")
                results[provider_type.value] = []
        
        return results
    
    async def health_check_all(self, credentials_map: Dict[ProviderType, ProviderCredentials]) -> Dict[str, ProviderStatus]:
        """Health check all providers."""
        results = {}
        
        for provider_type, credentials in credentials_map.items():
            try:
                async with self.get_provider_context(provider_type, credentials) as provider:
                    status = await provider.health_check()
                    results[provider_type.value] = status
            except Exception as e:
                logger.error(f"Health check failed for {provider_type.value}: {e}")
                results[provider_type.value] = ProviderStatus(
                    provider=provider_type,
                    is_available=False,
                    last_check=datetime.utcnow()
                )
        
        return results
    
    def get_cost_tracker(self):
        """Get the cost tracker instance."""
        return self._cost_tracker
    
    async def cleanup(self):
        """Cleanup all cached provider instances."""
        for instance in self._instances.values():
            try:
                await instance.close()
            except Exception as e:
                logger.error(f"Error closing provider instance: {e}")
        
        self._instances.clear()


# Global registry instance
_registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    return _registry


async def get_provider(provider_type: Union[ProviderType, str], credentials: ProviderCredentials) -> BaseProvider:
    """Convenience function to get a provider from the global registry."""
    if isinstance(provider_type, str):
        provider_type = ProviderType(provider_type)
    
    return await _registry.get_provider(provider_type, credentials)


def list_providers() -> List[str]:
    """Convenience function to list all registered providers."""
    return _registry.list_registered_providers()


def register_provider(provider_class: Type[BaseProvider], provider_type: ProviderType):
    """Convenience function to register a provider."""
    _registry.register_provider(provider_class, provider_type)


# Auto-register built-in providers when this module is imported
def _auto_register_providers():
    """Auto-register all available providers."""
    try:
        from .openai_provider import OpenAIProvider
        register_provider(OpenAIProvider, ProviderType.OPENAI)
    except ImportError:
        logger.warning("OpenAI provider not available")
    
    try:
        from .anthropic_provider import AnthropicProvider
        register_provider(AnthropicProvider, ProviderType.ANTHROPIC)
    except ImportError:
        logger.warning("Anthropic provider not available")
    
    try:
        from .google_provider import GoogleProvider
        register_provider(GoogleProvider, ProviderType.GOOGLE)
    except ImportError:
        logger.warning("Google provider not available")
    
    try:
        from .ollama_provider import OllamaProvider
        register_provider(OllamaProvider, ProviderType.OLLAMA)
    except ImportError:
        logger.warning("Ollama provider not available")
    
    try:
        from .cohere_provider import CohereProvider
        register_provider(CohereProvider, ProviderType.COHERE)
    except ImportError:
        logger.warning("Cohere provider not available")


# Auto-register providers when module is imported
_auto_register_providers()