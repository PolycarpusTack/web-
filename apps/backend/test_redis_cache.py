#!/usr/bin/env python3
"""
Test script to verify Redis caching functionality
"""
import asyncio
import time
from datetime import datetime
import logging
from typing import Dict, Any

from core.cache import cache_manager, CacheNamespaces

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_basic_operations():
    """Test basic cache operations."""
    logger.info("Testing basic cache operations...")
    
    # Test set and get
    test_key = "test_key"
    test_value = {"message": "Hello Redis!", "timestamp": datetime.utcnow().isoformat()}
    
    # Set value
    success = await cache_manager.set(CacheNamespaces.MODELS, test_key, test_value, ttl=60)
    assert success, "Failed to set cache value"
    logger.info("✓ Set operation successful")
    
    # Get value
    retrieved = await cache_manager.get(CacheNamespaces.MODELS, test_key)
    assert retrieved == test_value, f"Retrieved value doesn't match: {retrieved} != {test_value}"
    logger.info("✓ Get operation successful")
    
    # Check exists
    exists = await cache_manager.exists(CacheNamespaces.MODELS, test_key)
    assert exists, "Key should exist"
    logger.info("✓ Exists check successful")
    
    # Delete value
    deleted = await cache_manager.delete(CacheNamespaces.MODELS, test_key)
    assert deleted, "Failed to delete cache value"
    logger.info("✓ Delete operation successful")
    
    # Verify deletion
    retrieved_after_delete = await cache_manager.get(CacheNamespaces.MODELS, test_key)
    assert retrieved_after_delete is None, "Value should be None after deletion"
    logger.info("✓ Deletion verified")


async def test_performance():
    """Test cache performance and measure hit rates."""
    logger.info("\nTesting cache performance...")
    
    # Reset stats
    cache_manager.stats = {
        "hits": 0,
        "misses": 0,
        "sets": 0,
        "deletes": 0,
        "errors": 0
    }
    
    # Simulate model lookups
    model_ids = [f"model_{i}" for i in range(10)]
    
    # First pass - all misses (cold cache)
    start_time = time.time()
    for model_id in model_ids:
        result = await cache_manager.get(CacheNamespaces.MODELS, model_id)
        if result is None:
            # Simulate fetching from database
            model_data = {
                "id": model_id,
                "name": f"Test Model {model_id}",
                "provider": "ollama",
                "status": "available"
            }
            await cache_manager.set(CacheNamespaces.MODELS, model_id, model_data, ttl=300)
    
    cold_cache_time = time.time() - start_time
    logger.info(f"Cold cache time: {cold_cache_time:.3f}s")
    
    # Second pass - all hits (warm cache)
    start_time = time.time()
    for model_id in model_ids:
        result = await cache_manager.get(CacheNamespaces.MODELS, model_id)
        assert result is not None, f"Model {model_id} should be in cache"
    
    warm_cache_time = time.time() - start_time
    logger.info(f"Warm cache time: {warm_cache_time:.3f}s")
    logger.info(f"Performance improvement: {cold_cache_time/warm_cache_time:.1f}x faster")
    
    # Get stats
    stats = cache_manager.get_stats()
    logger.info(f"\nCache Statistics:")
    logger.info(f"  Hits: {stats['hits']}")
    logger.info(f"  Misses: {stats['misses']}")
    logger.info(f"  Hit Rate: {stats['hit_rate']:.1f}%")
    logger.info(f"  Backend: {stats['backend_type']}")


async def test_ttl_expiration():
    """Test TTL expiration."""
    logger.info("\nTesting TTL expiration...")
    
    # Set with short TTL
    test_key = "ttl_test"
    test_value = {"message": "This will expire soon"}
    
    await cache_manager.set(CacheNamespaces.MODELS, test_key, test_value, ttl=2)
    
    # Verify it exists
    result = await cache_manager.get(CacheNamespaces.MODELS, test_key)
    assert result == test_value, "Value should exist immediately after setting"
    logger.info("✓ Value exists before TTL expiration")
    
    # Wait for expiration
    logger.info("Waiting for TTL expiration...")
    await asyncio.sleep(3)
    
    # Verify it's gone
    result = await cache_manager.get(CacheNamespaces.MODELS, test_key)
    assert result is None, "Value should be None after TTL expiration"
    logger.info("✓ Value expired correctly")


async def test_namespace_isolation():
    """Test namespace isolation."""
    logger.info("\nTesting namespace isolation...")
    
    test_key = "shared_key"
    models_value = {"type": "model"}
    users_value = {"type": "user"}
    
    # Set same key in different namespaces
    await cache_manager.set(CacheNamespaces.MODELS, test_key, models_value)
    await cache_manager.set(CacheNamespaces.USERS, test_key, users_value)
    
    # Retrieve from different namespaces
    models_result = await cache_manager.get(CacheNamespaces.MODELS, test_key)
    users_result = await cache_manager.get(CacheNamespaces.USERS, test_key)
    
    assert models_result == models_value, "Models namespace value incorrect"
    assert users_result == users_value, "Users namespace value incorrect"
    logger.info("✓ Namespace isolation working correctly")


async def test_complex_data_types():
    """Test caching of complex data types."""
    logger.info("\nTesting complex data types...")
    
    complex_data = {
        "id": "test-123",
        "metadata": {
            "created_at": datetime.utcnow().isoformat(),
            "tags": ["ai", "model", "test"],
            "config": {
                "temperature": 0.7,
                "max_tokens": 2048,
                "top_p": 0.9
            }
        },
        "metrics": [
            {"name": "accuracy", "value": 0.95},
            {"name": "latency", "value": 125.5}
        ],
        "nested_lists": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    }
    
    # Set complex data
    await cache_manager.set(CacheNamespaces.ANALYTICS, "complex_test", complex_data)
    
    # Retrieve and verify
    retrieved = await cache_manager.get(CacheNamespaces.ANALYTICS, "complex_test")
    assert retrieved == complex_data, "Complex data not preserved correctly"
    logger.info("✓ Complex data types cached correctly")


async def main():
    """Run all cache tests."""
    logger.info("Starting Redis cache tests...")
    
    try:
        # Initialize cache manager
        await cache_manager.initialize()
        logger.info(f"Cache backend: {cache_manager.backend.__class__.__name__}")
        
        # Run tests
        await test_basic_operations()
        await test_performance()
        await test_ttl_expiration()
        await test_namespace_isolation()
        await test_complex_data_types()
        
        logger.info("\n✅ All cache tests passed!")
        
    except Exception as e:
        logger.error(f"\n❌ Cache test failed: {e}")
        raise
    finally:
        # Cleanup
        await cache_manager.shutdown()
        logger.info("Cache manager shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())