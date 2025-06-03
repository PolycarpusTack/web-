"""
Redis Caching Layer for Performance Optimization

This module provides a comprehensive caching system using Redis with fallback
to in-memory caching for development environments.
"""

import json
import logging
import hashlib
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import asyncio
import os

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from cachetools import TTLCache
import pickle

logger = logging.getLogger(__name__)


class CacheError(Exception):
    """Base exception for cache operations."""
    pass


class CacheBackend:
    """Base class for cache backends."""
    
    async def get(self, key: str) -> Optional[Any]:
        raise NotImplementedError
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        raise NotImplementedError
    
    async def clear(self) -> bool:
        raise NotImplementedError
    
    async def exists(self, key: str) -> bool:
        raise NotImplementedError


class RedisBackend(CacheBackend):
    """Redis cache backend for production use."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis_client = None
        self._connection_pool = None
        
    async def connect(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache backend connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
            return False
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.redis_client = None
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Failed to serialize value: {e}")
            raise CacheError(f"Serialization failed: {e}")
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            return pickle.loads(data)
        except Exception as e:
            logger.error(f"Failed to deserialize value: {e}")
            raise CacheError(f"Deserialization failed: {e}")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache."""
        if not self.redis_client:
            return None
            
        try:
            data = await self.redis_client.get(key)
            if data is None:
                return None
            return self._deserialize(data)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in Redis cache with TTL."""
        if not self.redis_client:
            return False
            
        try:
            serialized = self._serialize(value)
            await self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from Redis cache."""
        if not self.redis_client:
            return False
            
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all keys from Redis cache."""
        if not self.redis_client:
            return False
            
        try:
            await self.redis_client.flushdb()
            return True
        except Exception as e:
            logger.error(f"Redis clear error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache."""
        if not self.redis_client:
            return False
            
        try:
            result = await self.redis_client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False


class MemoryBackend(CacheBackend):
    """In-memory cache backend for development use."""
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        self.cache = TTLCache(maxsize=max_size, ttl=default_ttl)
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache."""
        async with self._lock:
            return self.cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in memory cache with TTL."""
        async with self._lock:
            try:
                # TTLCache doesn't support per-key TTL, so we use the default
                self.cache[key] = value
                return True
            except Exception as e:
                logger.error(f"Memory cache set error for key {key}: {e}")
                return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from memory cache."""
        async with self._lock:
            try:
                if key in self.cache:
                    del self.cache[key]
                    return True
                return False
            except Exception as e:
                logger.error(f"Memory cache delete error for key {key}: {e}")
                return False
    
    async def clear(self) -> bool:
        """Clear all keys from memory cache."""
        async with self._lock:
            try:
                self.cache.clear()
                return True
            except Exception as e:
                logger.error(f"Memory cache clear error: {e}")
                return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache."""
        async with self._lock:
            return key in self.cache


class CacheManager:
    """
    Main cache manager that provides high-level caching operations.
    Automatically selects between Redis and memory backend based on availability.
    """
    
    def __init__(self, redis_url: str = None, fallback_to_memory: bool = True):
        self.backend = None
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.fallback_to_memory = fallback_to_memory
        self._initialized = False
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0
        }
    
    async def initialize(self):
        """Initialize the cache backend."""
        if self._initialized:
            return
        
        # Try Redis first if available
        if REDIS_AVAILABLE:
            redis_backend = RedisBackend(self.redis_url)
            if await redis_backend.connect():
                self.backend = redis_backend
                logger.info("Using Redis cache backend")
                self._initialized = True
                return
        
        # Fallback to memory cache
        if self.fallback_to_memory:
            self.backend = MemoryBackend()
            logger.info("Using memory cache backend")
            self._initialized = True
        else:
            raise CacheError("No cache backend available")
    
    async def shutdown(self):
        """Shutdown the cache backend."""
        if self.backend and hasattr(self.backend, 'disconnect'):
            await self.backend.disconnect()
        self._initialized = False
    
    def _generate_key(self, namespace: str, key: str, **kwargs) -> str:
        """Generate a consistent cache key."""
        if kwargs:
            # Include parameters in key for cache differentiation
            params_str = json.dumps(sorted(kwargs.items()), sort_keys=True)
            key_data = f"{namespace}:{key}:{params_str}"
        else:
            key_data = f"{namespace}:{key}"
        
        # Hash long keys to keep them manageable
        if len(key_data) > 200:
            key_hash = hashlib.md5(key_data.encode()).hexdigest()
            return f"{namespace}:hash:{key_hash}"
        
        return key_data
    
    async def get(self, namespace: str, key: str, **kwargs) -> Optional[Any]:
        """Get value from cache."""
        if not self._initialized:
            await self.initialize()
        
        cache_key = self._generate_key(namespace, key, **kwargs)
        
        try:
            value = await self.backend.get(cache_key)
            if value is not None:
                self.stats["hits"] += 1
                logger.debug(f"Cache hit for key: {cache_key}")
                return value
            else:
                self.stats["misses"] += 1
                logger.debug(f"Cache miss for key: {cache_key}")
                return None
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache get error for key {cache_key}: {e}")
            return None
    
    async def set(self, namespace: str, key: str, value: Any, ttl: int = 300, **kwargs) -> bool:
        """Set value in cache with TTL."""
        if not self._initialized:
            await self.initialize()
        
        cache_key = self._generate_key(namespace, key, **kwargs)
        
        try:
            success = await self.backend.set(cache_key, value, ttl)
            if success:
                self.stats["sets"] += 1
                logger.debug(f"Cache set for key: {cache_key}")
            return success
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache set error for key {cache_key}: {e}")
            return False
    
    async def delete(self, namespace: str, key: str, **kwargs) -> bool:
        """Delete key from cache."""
        if not self._initialized:
            await self.initialize()
        
        cache_key = self._generate_key(namespace, key, **kwargs)
        
        try:
            success = await self.backend.delete(cache_key)
            if success:
                self.stats["deletes"] += 1
                logger.debug(f"Cache delete for key: {cache_key}")
            return success
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Cache delete error for key {cache_key}: {e}")
            return False
    
    async def clear_namespace(self, namespace: str) -> bool:
        """Clear all keys in a namespace (Redis only)."""
        if not self._initialized:
            await self.initialize()
        
        # This is a simple implementation - in production you might want
        # to use Redis SCAN command for better performance
        if isinstance(self.backend, RedisBackend) and self.backend.redis_client:
            try:
                pattern = f"{namespace}:*"
                keys = []
                async for key in self.backend.redis_client.scan_iter(match=pattern):
                    keys.append(key)
                
                if keys:
                    await self.backend.redis_client.delete(*keys)
                return True
            except Exception as e:
                logger.error(f"Cache clear namespace error for {namespace}: {e}")
                return False
        
        return False
    
    async def exists(self, namespace: str, key: str, **kwargs) -> bool:
        """Check if key exists in cache."""
        if not self._initialized:
            await self.initialize()
        
        cache_key = self._generate_key(namespace, key, **kwargs)
        return await self.backend.exists(cache_key)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.stats,
            "hit_rate": round(hit_rate, 2),
            "backend_type": type(self.backend).__name__ if self.backend else None
        }


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions for common cache operations
async def get_cached(namespace: str, key: str, **kwargs) -> Optional[Any]:
    """Get value from cache."""
    return await cache_manager.get(namespace, key, **kwargs)


async def set_cached(namespace: str, key: str, value: Any, ttl: int = 300, **kwargs) -> bool:
    """Set value in cache."""
    return await cache_manager.set(namespace, key, value, ttl, **kwargs)


async def delete_cached(namespace: str, key: str, **kwargs) -> bool:
    """Delete key from cache."""
    return await cache_manager.delete(namespace, key, **kwargs)


async def clear_cache_namespace(namespace: str) -> bool:
    """Clear all keys in namespace."""
    return await cache_manager.clear_namespace(namespace)


# Cache decorators for functions
def cached(namespace: str, ttl: int = 300, key_func=None):
    """
    Decorator to cache function results.
    
    Args:
        namespace: Cache namespace
        ttl: Time to live in seconds
        key_func: Function to generate cache key from arguments
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default key generation from function name and arguments
                args_str = "_".join(str(arg) for arg in args)
                kwargs_str = "_".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{func.__name__}_{args_str}_{kwargs_str}"
            
            # Try to get from cache
            cached_result = await get_cached(namespace, cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await set_cached(namespace, cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


# Common cache namespaces
class CacheNamespaces:
    MODELS = "models"
    CONVERSATIONS = "conversations"
    USERS = "users"
    PROVIDERS = "providers"
    WORKSPACES = "workspaces"
    AUDIT_LOGS = "audit_logs"
    PERMISSIONS = "permissions"
    FILES = "files"
    ANALYTICS = "analytics"