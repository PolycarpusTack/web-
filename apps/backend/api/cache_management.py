"""
Cache Management API

Provides endpoints for managing the Redis caching layer and monitoring cache performance.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from db.database import get_db
from db.crud import user_has_permission
from auth.jwt import get_current_user
from auth.schemas import UserResponse
from core.cache import cache_manager, CacheNamespaces

router = APIRouter(prefix="/api/cache", tags=["Cache Management"])


class CacheStats(BaseModel):
    """Cache statistics response model."""
    hits: int
    misses: int
    sets: int
    deletes: int
    errors: int
    hit_rate: float
    backend_type: Optional[str]
    total_requests: int


class CacheOperation(BaseModel):
    """Cache operation request model."""
    namespace: str
    key: str
    value: Optional[Any] = None
    ttl: Optional[int] = 300


class CacheResponse(BaseModel):
    """Cache operation response model."""
    success: bool
    message: str
    data: Optional[Any] = None


@router.get("/stats", response_model=CacheStats)
async def get_cache_stats(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get cache performance statistics."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "system.monitor")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    stats = cache_manager.get_stats()
    total_requests = stats["hits"] + stats["misses"]
    
    return CacheStats(
        hits=stats["hits"],
        misses=stats["misses"],
        sets=stats["sets"],
        deletes=stats["deletes"],
        errors=stats["errors"],
        hit_rate=stats["hit_rate"],
        backend_type=stats["backend_type"],
        total_requests=total_requests
    )


@router.get("/health")
async def cache_health_check(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check cache backend health."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "system.monitor")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Try a simple cache operation
        test_key = "health_check"
        test_value = {"timestamp": "test", "status": "ok"}
        
        # Test set
        set_success = await cache_manager.set("health", test_key, test_value, ttl=60)
        if not set_success:
            return {"status": "unhealthy", "error": "Failed to set test value"}
        
        # Test get
        retrieved_value = await cache_manager.get("health", test_key)
        if retrieved_value != test_value:
            return {"status": "unhealthy", "error": "Failed to retrieve test value"}
        
        # Test delete
        delete_success = await cache_manager.delete("health", test_key)
        if not delete_success:
            return {"status": "warning", "message": "Cache working but failed to cleanup test data"}
        
        return {
            "status": "healthy",
            "backend": cache_manager.backend.__class__.__name__ if cache_manager.backend else None,
            "initialized": cache_manager._initialized
        }
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@router.post("/clear/{namespace}")
async def clear_cache_namespace(
    namespace: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Clear all cache entries in a specific namespace."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "system.manage")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Validate namespace
    valid_namespaces = [
        CacheNamespaces.MODELS,
        CacheNamespaces.CONVERSATIONS,
        CacheNamespaces.USERS,
        CacheNamespaces.PROVIDERS,
        CacheNamespaces.WORKSPACES,
        CacheNamespaces.AUDIT_LOGS,
        CacheNamespaces.PERMISSIONS,
        CacheNamespaces.FILES,
        CacheNamespaces.ANALYTICS
    ]
    
    if namespace not in valid_namespaces:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid namespace. Valid namespaces: {valid_namespaces}"
        )
    
    try:
        success = await cache_manager.clear_namespace(namespace)
        if success:
            return {"message": f"Successfully cleared cache namespace: {namespace}"}
        else:
            return {"message": f"Failed to clear cache namespace: {namespace}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache clear error: {str(e)}")


@router.get("/key/{namespace}/{key}")
async def get_cache_key(
    namespace: str,
    key: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific cache key value."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "system.monitor")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        value = await cache_manager.get(namespace, key)
        exists = await cache_manager.exists(namespace, key)
        
        return {
            "namespace": namespace,
            "key": key,
            "exists": exists,
            "value": value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache get error: {str(e)}")


@router.post("/key/{namespace}/{key}")
async def set_cache_key(
    namespace: str,
    key: str,
    operation: CacheOperation,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Set a specific cache key value."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "system.manage")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    if operation.value is None:
        raise HTTPException(status_code=400, detail="Value is required for set operation")
    
    try:
        success = await cache_manager.set(
            namespace, 
            key, 
            operation.value, 
            ttl=operation.ttl or 300
        )
        
        if success:
            return CacheResponse(
                success=True,
                message=f"Successfully set cache key: {namespace}:{key}"
            )
        else:
            return CacheResponse(
                success=False,
                message=f"Failed to set cache key: {namespace}:{key}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache set error: {str(e)}")


@router.delete("/key/{namespace}/{key}")
async def delete_cache_key(
    namespace: str,
    key: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a specific cache key."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "system.manage")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        success = await cache_manager.delete(namespace, key)
        
        if success:
            return CacheResponse(
                success=True,
                message=f"Successfully deleted cache key: {namespace}:{key}"
            )
        else:
            return CacheResponse(
                success=False,
                message=f"Cache key not found or failed to delete: {namespace}:{key}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache delete error: {str(e)}")


@router.get("/namespaces")
async def list_cache_namespaces(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all available cache namespaces."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "system.monitor")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    namespaces = [
        {"name": CacheNamespaces.MODELS, "description": "Model definitions and metadata"},
        {"name": CacheNamespaces.CONVERSATIONS, "description": "Conversation data and messages"},
        {"name": CacheNamespaces.USERS, "description": "User profiles and settings"},
        {"name": CacheNamespaces.PROVIDERS, "description": "AI provider configurations and status"},
        {"name": CacheNamespaces.WORKSPACES, "description": "Workspace data and member information"},
        {"name": CacheNamespaces.AUDIT_LOGS, "description": "Audit logs and compliance data"},
        {"name": CacheNamespaces.PERMISSIONS, "description": "RBAC permissions and roles"},
        {"name": CacheNamespaces.FILES, "description": "File metadata and analysis results"},
        {"name": CacheNamespaces.ANALYTICS, "description": "Analytics and usage metrics"}
    ]
    
    return {"namespaces": namespaces}


@router.post("/warm-up")
async def warm_up_cache(
    namespaces: Optional[List[str]] = Query(None, description="Specific namespaces to warm up"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Warm up cache with frequently accessed data."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "system.manage")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        warmed_items = 0
        
        # Warm up models cache
        if not namespaces or CacheNamespaces.MODELS in namespaces:
            from db.crud import get_models
            models = await get_models(db)
            for model in models[:20]:  # Limit to prevent excessive memory usage
                await cache_manager.set(
                    CacheNamespaces.MODELS, 
                    f"model_{model.id}", 
                    {
                        "id": model.id,
                        "name": model.name,
                        "provider": model.provider,
                        "status": model.status
                    },
                    ttl=1800  # 30 minutes
                )
                warmed_items += 1
        
        # Warm up users cache (basic info only)
        if not namespaces or CacheNamespaces.USERS in namespaces:
            from db.crud import get_users
            users = await get_users(db, limit=50)
            for user in users:
                await cache_manager.set(
                    CacheNamespaces.USERS,
                    f"user_{user.id}",
                    {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "is_active": user.is_active
                    },
                    ttl=900  # 15 minutes
                )
                warmed_items += 1
        
        # Warm up workspaces cache
        if not namespaces or CacheNamespaces.WORKSPACES in namespaces:
            from db.crud import get_workspaces
            workspaces = await get_workspaces(db, limit=20)
            for workspace in workspaces:
                await cache_manager.set(
                    CacheNamespaces.WORKSPACES,
                    f"workspace_{workspace.id}",
                    {
                        "id": workspace.id,
                        "name": workspace.name,
                        "display_name": workspace.display_name,
                        "plan": workspace.plan,
                        "is_active": workspace.is_active
                    },
                    ttl=1200  # 20 minutes
                )
                warmed_items += 1
        
        return {
            "message": "Cache warm-up completed",
            "warmed_items": warmed_items,
            "namespaces": namespaces or ["all"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cache warm-up error: {str(e)}")


@router.get("/metrics")
async def get_cache_metrics(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed cache metrics and performance data."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "system.monitor")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    stats = cache_manager.get_stats()
    
    return {
        "performance": {
            "hit_rate": stats["hit_rate"],
            "total_requests": stats["hits"] + stats["misses"],
            "cache_efficiency": "excellent" if stats["hit_rate"] > 80 else "good" if stats["hit_rate"] > 60 else "needs_improvement"
        },
        "operations": {
            "hits": stats["hits"],
            "misses": stats["misses"],
            "sets": stats["sets"],
            "deletes": stats["deletes"],
            "errors": stats["errors"]
        },
        "backend": {
            "type": stats["backend_type"],
            "status": "connected" if cache_manager._initialized else "disconnected"
        },
        "recommendations": [
            "Consider increasing TTL for frequently accessed data" if stats["hit_rate"] < 70 else "Cache performance is optimal",
            "Monitor error rate" if stats["errors"] > 10 else "Error rate is acceptable",
            "Consider cache warm-up strategies" if stats["misses"] > stats["hits"] else "Cache utilization is good"
        ]
    }