"""
Caching utilities for improving API performance.
This module provides a Redis-based caching system for frequently accessed data.
"""

from typing import Any, Callable, Dict, Generic, List, Optional, Type, TypeVar, Union
import json
import hashlib
import inspect
import logging
import time
from functools import wraps
import redis.asyncio as redis
from pydantic import BaseModel

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for generic cache
T = TypeVar('T')

# Redis connection
redis_client = None

async def init_redis(redis_url: str):
    """
    Initialize the Redis client.
    
    Args:
        redis_url: Redis connection URL (redis://host:port/db)
    """
    global redis_client
    try:
        redis_client = redis.from_url(redis_url)
        # Test connection
        await redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {str(e)}")
        redis_client = None

async def close_redis():
    """Close the Redis connection."""
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None
        logger.info("Redis connection closed")

class MemoryCache:
    """Simple in-memory cache for development or when Redis is unavailable."""
    
    def __init__(self):
        self.cache = {}
        self.ttl = {}
        
    async def get(self, key: str) -> Any:
        """Get a value from the cache."""
        # Check if key exists and TTL hasn't expired
        if key in self.cache and key in self.ttl:
            if self.ttl[key] > time.time():
                return self.cache[key]
            else:
                # Expired, remove from cache
                del self.cache[key]
                del self.ttl[key]
        return None
        
    async def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        """Set a value in the cache with TTL in seconds."""
        self.cache[key] = value
        self.ttl[key] = time.time() + ttl
        return True
        
    async def delete(self, key: str) -> bool:
        """Delete a value from the cache."""
        if key in self.cache:
            del self.cache[key]
            if key in self.ttl:
                del self.ttl[key]
            return True
        return False
        
    async def clear(self) -> bool:
        """Clear the entire cache."""
        self.cache.clear()
        self.ttl.clear()
        return True

# Create memory cache for fallback
memory_cache = MemoryCache()

async def get_cache_client():
    """Get the appropriate cache client (Redis or in-memory)."""
    global redis_client
    if redis_client:
        try:
            # Test connection
            await redis_client.ping()
            return redis_client
        except Exception:
            logger.warning("Redis connection failed, falling back to in-memory cache")
            return memory_cache
    return memory_cache

def generate_cache_key(
    prefix: str,
    func_name: str,
    args: tuple,
    kwargs: Dict[str, Any]
) -> str:
    """
    Generate a consistent cache key based on function name and arguments.
    
    Args:
        prefix: Cache key prefix
        func_name: Function name
        args: Positional arguments
        kwargs: Keyword arguments
        
    Returns:
        A unique cache key
    """
    # Convert args and kwargs to a string representation
    arg_string = json.dumps(args, sort_keys=True)
    kwarg_string = json.dumps(kwargs, sort_keys=True)
    
    # Generate a hash of the arguments
    arg_hash = hashlib.md5(f"{arg_string}:{kwarg_string}".encode()).hexdigest()
    
    # Create a unique cache key
    return f"{prefix}:{func_name}:{arg_hash}"

def cached(
    ttl: int = 60,
    key_prefix: str = "cache",
    skip_args: int = 0,
    cache_none: bool = False
):
    """
    Cache decorator for async functions.
    
    Args:
        ttl: Time to live in seconds (default: 60)
        key_prefix: Cache key prefix (default: "cache")
        skip_args: Number of arguments to skip when generating the cache key (default: 0)
            Useful for skipping 'self' or 'cls' arguments in class methods
        cache_none: Whether to cache None values (default: False)
            
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get cache client
            cache = await get_cache_client()
            
            # Generate cache key
            func_name = func.__name__
            cache_key = generate_cache_key(
                key_prefix,
                func_name,
                args[skip_args:] if skip_args > 0 else args,
                kwargs
            )
            
            # Try to get from cache
            try:
                cached_value = await cache.get(cache_key)
                
                if cached_value is not None:
                    # Deserialize JSON
                    try:
                        value = json.loads(cached_value)
                        logger.debug(f"Cache hit for {func_name}: {cache_key}")
                        return value
                    except json.JSONDecodeError:
                        # If we can't deserialize, return the raw value
                        logger.debug(f"Cache hit (raw) for {func_name}: {cache_key}")
                        return cached_value
            except Exception as e:
                logger.warning(f"Cache get error for {func_name}: {str(e)}")
            
            # Cache miss, call the function
            logger.debug(f"Cache miss for {func_name}: {cache_key}")
            result = await func(*args, **kwargs)
            
            # Cache the result if not None or if cache_none is True
            if result is not None or cache_none:
                try:
                    # Serialize to JSON
                    json_result = json.dumps(result)
                    await cache.set(cache_key, json_result, ttl)
                except Exception as e:
                    logger.warning(f"Cache set error for {func_name}: {str(e)}")
            
            return result
        
        return wrapper
    
    return decorator

async def invalidate_cache(
    key_prefix: str,
    func_name: Optional[str] = None,
    exact_key: Optional[str] = None
) -> bool:
    """
    Invalidate cache entries based on prefix and function name.
    
    Args:
        key_prefix: Cache key prefix
        func_name: Optional function name to invalidate
        exact_key: Optional exact key to invalidate
        
    Returns:
        True if successful, False otherwise
    """
    try:
        cache = await get_cache_client()
        
        if exact_key:
            # Delete exact key
            await cache.delete(exact_key)
            return True
            
        if isinstance(cache, redis.Redis):
            # For Redis, we can use pattern matching
            pattern = f"{key_prefix}:{func_name}:*" if func_name else f"{key_prefix}:*"
            
            # Get all keys matching the pattern
            keys = await cache.keys(pattern)
            
            if keys:
                # Delete all matching keys
                await cache.delete(*keys)
                
            return True
        else:
            # For memory cache, we don't have pattern matching
            # We'd need to implement a more manual approach
            if func_name:
                # Not ideal, but scan all keys and delete matching ones
                for key in list(memory_cache.cache.keys()):
                    if key.startswith(f"{key_prefix}:{func_name}:"):
                        await memory_cache.delete(key)
            else:
                # Clear all keys with the prefix
                for key in list(memory_cache.cache.keys()):
                    if key.startswith(f"{key_prefix}:"):
                        await memory_cache.delete(key)
                        
            return True
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        return False

# Cache utility for model-based caching
class ModelCache(Generic[T]):
    """
    A utility class for caching model objects.
    
    This provides a more structured approach for caching model objects
    with automatic serialization and deserialization.
    
    Example usage:
    ```
    user_cache = ModelCache("user", UserResponse, ttl=300)
    
    # Cache and retrieve
    user = await user_cache.get("user123")
    if not user:
        user = await get_user_from_db("user123")
        await user_cache.set("user123", user)
    ```
    """
    
    def __init__(
        self,
        prefix: str,
        model_class: Type[BaseModel],
        ttl: int = 60
    ):
        self.prefix = prefix
        self.model_class = model_class
        self.ttl = ttl
        
    async def get(self, key: str) -> Optional[T]:
        """
        Get a model from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached model or None if not found
        """
        cache = await get_cache_client()
        full_key = f"{self.prefix}:{key}"
        
        try:
            cached_value = await cache.get(full_key)
            
            if cached_value:
                # Deserialize JSON
                data = json.loads(cached_value)
                return self.model_class.parse_obj(data)
        except Exception as e:
            logger.warning(f"Cache get error for {full_key}: {str(e)}")
            
        return None
        
    async def set(self, key: str, value: T) -> bool:
        """
        Set a model in the cache.
        
        Args:
            key: The cache key
            value: The model to cache
            
        Returns:
            True if successful, False otherwise
        """
        cache = await get_cache_client()
        full_key = f"{self.prefix}:{key}"
        
        try:
            # Serialize to JSON
            json_data = value.json()
            await cache.set(full_key, json_data, self.ttl)
            return True
        except Exception as e:
            logger.warning(f"Cache set error for {full_key}: {str(e)}")
            return False
            
    async def delete(self, key: str) -> bool:
        """
        Delete a model from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            True if successful, False otherwise
        """
        cache = await get_cache_client()
        full_key = f"{self.prefix}:{key}"
        
        try:
            await cache.delete(full_key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for {full_key}: {str(e)}")
            return False
            
    async def invalidate_all(self) -> bool:
        """
        Invalidate all cached models with this prefix.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            return await invalidate_cache(self.prefix)
        except Exception as e:
            logger.error(f"Error invalidating cache: {str(e)}")
            return False
