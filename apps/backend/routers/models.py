"""
Models router with WebSocket integration for real-time status updates
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import httpx
import logging
import time

from db.database import get_db
from db import crud
from auth.jwt import get_current_user
from db.models import User
from core.websocket import manager
from core.cache import cache_manager, cached, CacheNamespaces
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models
class ModelInfo(BaseModel):
    id: str
    name: str
    provider: str
    size: Optional[str] = None
    status: str
    is_active: bool
    is_local: bool
    context_window: int
    description: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ModelListResponse(BaseModel):
    models: List[ModelInfo]
    total: int


class StartStopRequest(BaseModel):
    model_id: str


class ModelStatusUpdate(BaseModel):
    model_id: str
    status: str
    details: Optional[Dict[str, Any]] = None


@router.get("/", response_model=ModelListResponse)
async def list_models(
    provider: Optional[str] = Query(None, description="Filter by provider"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_local: Optional[bool] = Query(None, description="Filter by local/external"),
    search: Optional[str] = Query(None, description="Search in name or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of available models with filtering"""
    # Generate cache key based on parameters
    cache_key = f"list_{provider}_{is_active}_{is_local}_{search}_{skip}_{limit}"
    
    # Try to get from cache first
    cached_result = await cache_manager.get(CacheNamespaces.MODELS, cache_key)
    if cached_result is not None:
        logger.debug(f"Cache hit for models list: {cache_key}")
        return cached_result
    
    try:
        # Build filters
        filters = {}
        if provider:
            filters["provider"] = provider
        if is_active is not None:
            filters["is_active"] = is_active
        if is_local is not None:
            filters["is_local"] = is_local
        
        # Get models from database
        models = await crud.get_models(db, filters, skip, limit)
        total = await crud.count_models(db, filters)
        
        # If local models requested, also check Ollama
        if is_local is None or is_local:
            try:
                # Get Ollama models
                from main import app
                response = await app.state.http_client.get("/api/tags")
                
                if response.status_code == 200:
                    ollama_data = response.json()
                    ollama_models = ollama_data.get("models", [])
                    
                    # Update database with Ollama models
                    for ollama_model in ollama_models:
                        model_id = ollama_model["name"]
                        
                        # Check if model exists in DB
                        db_model = await crud.get_model(db, model_id)
                        
                        if not db_model:
                            # Create new model entry
                            await crud.create_model(db, {
                                "id": model_id,
                                "name": model_id.split(":")[0].title(),
                                "provider": "ollama",
                                "size": f"{ollama_model.get('size', 0) / (1024**3):.2f} GB",
                                "is_active": True,
                                "is_local": True,
                                "status": "available",
                                "context_window": 4096,
                                "description": f"Ollama model {model_id}",
                                "metadata": {
                                    "digest": ollama_model.get("digest"),
                                    "modified_at": ollama_model.get("modified_at"),
                                }
                            })
                        else:
                            # Update existing model
                            await crud.update_model(db, model_id, {
                                "size": f"{ollama_model.get('size', 0) / (1024**3):.2f} GB",
                                "status": "available",
                                "metadata": {
                                    **db_model.metadata,
                                    "digest": ollama_model.get("digest"),
                                    "modified_at": ollama_model.get("modified_at"),
                                }
                            })
                    
                    # Refresh models list
                    models = await crud.get_models(db, filters, skip, limit)
                    total = await crud.count_models(db, filters)
                    
            except Exception as e:
                logger.error(f"Failed to fetch Ollama models: {e}")
        
        # Convert to response format
        model_list = [
            ModelInfo(
                id=model.id,
                name=model.name,
                provider=model.provider,
                size=model.size,
                status=model.status,
                is_active=model.is_active,
                is_local=model.is_local,
                context_window=model.context_window,
                description=model.description,
                metadata=model.metadata or {}
            )
            for model in models
        ]
        
        # Apply search filter if provided
        if search:
            search_lower = search.lower()
            model_list = [
                m for m in model_list
                if search_lower in m.name.lower() or 
                   (m.description and search_lower in m.description.lower())
            ]
            total = len(model_list)
        
        result = ModelListResponse(models=model_list, total=total)
        
        # Cache the result with 5 minute TTL
        await cache_manager.set(CacheNamespaces.MODELS, cache_key, result, ttl=300)
        logger.debug(f"Cached models list: {cache_key}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_id}", response_model=ModelInfo)
async def get_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific model details"""
    # Try cache first
    cache_key = f"model_{model_id}"
    cached_model = await cache_manager.get(CacheNamespaces.MODELS, cache_key)
    if cached_model is not None:
        logger.debug(f"Cache hit for model: {model_id}")
        return cached_model
    
    model = await crud.get_model(db, model_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    result = ModelInfo(
        id=model.id,
        name=model.name,
        provider=model.provider,
        size=model.size,
        status=model.status,
        is_active=model.is_active,
        is_local=model.is_local,
        context_window=model.context_window,
        description=model.description,
        metadata=model.metadata or {}
    )
    
    # Cache the result
    await cache_manager.set(CacheNamespaces.MODELS, cache_key, result, ttl=600)
    logger.debug(f"Cached model: {model_id}")
    
    return result


@router.post("/start")
async def start_model(
    request: StartStopRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a model (load into memory)"""
    model = await crud.get_model(db, request.model_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    if not model.is_local:
        raise HTTPException(status_code=400, detail="Can only start local models")
    
    # Send status update via WebSocket
    await manager.send_model_update(
        request.model_id,
        "starting",
        {"message": "Loading model into memory..."}
    )
    
    try:
        # Start model by making a minimal request to Ollama
        from main import app
        
        logger.info(f"Starting model {request.model_id}")
        
        # Use generate endpoint to load the model
        response = await app.state.http_client.post(
            "/api/generate",
            json={
                "model": request.model_id,
                "prompt": "test",
                "stream": False,
                "options": {"num_predict": 1}
            },
            timeout=60  # Give it more time to load
        )
        
        if response.status_code == 200:
            # Update model status in database
            await crud.update_model(db, request.model_id, {"status": "running"})
            
            # Clear model cache to reflect status change
            await cache_manager.delete(CacheNamespaces.MODELS, f"model_{request.model_id}")
            await cache_manager.clear_namespace(CacheNamespaces.MODELS)
            
            # Send success update via WebSocket
            await manager.send_model_update(
                request.model_id,
                "running",
                {"message": "Model loaded successfully"}
            )
            
            return {
                "status": "success",
                "message": f"Model {request.model_id} started successfully",
                "model_id": request.model_id
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to start model: {response.text}"
            )
            
    except httpx.RequestError as e:
        logger.error(f"Failed to start model {request.model_id}: {e}")
        
        # Send error update via WebSocket
        await manager.send_model_update(
            request.model_id,
            "error",
            {"message": f"Failed to start model: {str(e)}"}
        )
        
        raise HTTPException(status_code=503, detail="Ollama service unavailable")
    except Exception as e:
        logger.error(f"Unexpected error starting model {request.model_id}: {e}")
        
        # Send error update via WebSocket
        await manager.send_model_update(
            request.model_id,
            "error",
            {"message": f"Unexpected error: {str(e)}"}
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_model(
    request: StartStopRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Stop a model (unload from memory)"""
    model = await crud.get_model(db, request.model_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    if not model.is_local:
        raise HTTPException(status_code=400, detail="Can only stop local models")
    
    # Note: Ollama doesn't have a direct stop/unload endpoint
    # In practice, models are unloaded automatically after inactivity
    
    # Update model status in database
    await crud.update_model(db, request.model_id, {"status": "stopped"})
    
    # Clear model cache to reflect status change
    await cache_manager.delete(CacheNamespaces.MODELS, f"model_{request.model_id}")
    await cache_manager.clear_namespace(CacheNamespaces.MODELS)
    
    # Send status update via WebSocket
    await manager.send_model_update(
        request.model_id,
        "stopped",
        {"message": "Model unloaded"}
    )
    
    return {
        "status": "success",
        "message": f"Model {request.model_id} stopped",
        "model_id": request.model_id
    }


@router.post("/pull/{model_name}")
async def pull_model(
    model_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Pull a new model from Ollama registry"""
    # Send initial status via WebSocket
    await manager.send_model_update(
        model_name,
        "downloading",
        {"message": "Starting model download..."}
    )
    
    try:
        from main import app
        
        # Start pulling the model
        response = await app.state.http_client.post(
            "/api/pull",
            json={"name": model_name, "stream": False},
            timeout=300  # 5 minutes timeout for large models
        )
        
        if response.status_code == 200:
            # Create model entry in database
            await crud.create_model(db, {
                "id": model_name,
                "name": model_name.split(":")[0].title(),
                "provider": "ollama",
                "is_active": True,
                "is_local": True,
                "status": "available",
                "context_window": 4096,
                "description": f"Ollama model {model_name}",
            })
            
            # Send success update via WebSocket
            await manager.send_model_update(
                model_name,
                "available",
                {"message": "Model downloaded successfully"}
            )
            
            return {
                "status": "success",
                "message": f"Model {model_name} pulled successfully",
                "model_id": model_name
            }
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Failed to pull model: {response.text}"
            )
            
    except Exception as e:
        logger.error(f"Failed to pull model {model_name}: {e}")
        
        # Send error update via WebSocket
        await manager.send_model_update(
            model_name,
            "error",
            {"message": f"Failed to download model: {str(e)}"}
        )
        
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{model_id}")
async def delete_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a model"""
    model = await crud.get_model(db, model_id)
    
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    if model.is_local:
        try:
            # Delete from Ollama
            from main import app
            
            response = await app.state.http_client.delete(
                f"/api/delete",
                json={"name": model_id}
            )
            
            if response.status_code != 200:
                logger.warning(f"Failed to delete model from Ollama: {response.text}")
        except Exception as e:
            logger.error(f"Error deleting model from Ollama: {e}")
    
    # Delete from database
    await crud.delete_model(db, model_id)
    
    # Clear model cache
    await cache_manager.delete(CacheNamespaces.MODELS, f"model_{model_id}")
    await cache_manager.clear_namespace(CacheNamespaces.MODELS)
    
    # Send update via WebSocket
    await manager.send_model_update(
        model_id,
        "deleted",
        {"message": "Model deleted"}
    )
    
    return {
        "status": "success",
        "message": f"Model {model_id} deleted"
    }


@router.get("/status/running")
async def get_running_models(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get list of currently running models"""
    try:
        from main import app
        
        # Get running models from Ollama
        response = await app.state.http_client.get("/api/ps")
        
        if response.status_code == 200:
            data = response.json()
            running_models = data.get("models", [])
            
            # Update database status
            for model_info in running_models:
                model_name = model_info.get("name")
                if model_name:
                    await crud.update_model(db, model_name, {"status": "running"})
            
            return {
                "models": running_models,
                "count": len(running_models)
            }
        else:
            return {"models": [], "count": 0}
            
    except Exception as e:
        logger.error(f"Failed to get running models: {e}")
        return {"models": [], "count": 0, "error": str(e)}