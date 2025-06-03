# main.py

from fastapi import FastAPI, HTTPException, APIRouter, Depends, status, WebSocket, Request
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import httpx
import logging
import logging.config
import uuid
import time
import os
from contextlib import asynccontextmanager
from prometheus_fastapi_instrumentator import Instrumentator
from cachetools import TTLCache

# Database imports
from sqlalchemy.ext.asyncio import AsyncSession
from db.database import get_db, async_engine, init_async_db, close_async_db
from db.models import Base, User
from db import crud
from db.init_db import init_db

# Authentication imports
from auth.router import router as auth_router
from auth.jwt import get_current_user, get_current_active_user
from auth.api_keys import router as api_keys_router
from auth.rbac_router import router as rbac_router
from auth.workspace_router import router as workspace_router
from auth.invitation_router import router as invitation_router
from auth.compliance_router import router as compliance_router

# File handling imports
from files.router import router as files_router

# Pipeline imports - temporarily disabled due to import conflicts
# from pipeline.router import router as pipeline_router

# Advanced search imports
from api.model_search import router as model_search_router

# Analytics imports
from api.model_analytics import router as analytics_router

# Cache management imports
from api.cache_management import router as cache_management_router

# Job management imports - temporarily disabled due to syntax error
# from api.job_management import router as job_management_router

# Streaming chat imports
from api.streaming_chat import router as streaming_chat_router

# Conversation management imports
from api.conversation_management import router as conversation_management_router

# Message export imports
from api.message_export import router as message_export_router

# WebSocket imports
from api.websocket_endpoints import router as websocket_router

# Pipeline execution imports
from api.pipeline_execution import router as pipeline_execution_router

# Help system imports
from api.help_system import router as help_system_router

# --- Configuration ---
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    ollama_url: str = "http://localhost:11434"
    api_keys: List[str] = ["SECRET_KEY"]
    cors_origins: List[str] = ["http://localhost:3000"]
    rate_limit: str = "10/minute"
    enable_metrics: bool = True
    cache_ttl: int = 300  # 5 minutes
    api_base_url: str = "http://localhost:8000"
    upload_dir: str = "./uploads"

    class Config:
        env_file = ".env"
        env_prefix = "EMMP_"

settings = Settings()

# --- Advanced Logging Setup ---
logging.config.dictConfig({
    "version": 1,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "stream": "ext://sys.stdout"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"]
    }
})
logger = logging.getLogger(__name__)

# --- Security ---
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def validate_api_key_or_jwt(
    api_key: Optional[str] = Depends(api_key_header),
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_current_user)
):
    """
    Validate either an API key or a JWT token.
    This allows both authentication methods to be used.
    """
    # If we have a valid JWT user, authentication is successful
    if user:
        return
        
    # Check built-in API keys (for development/testing)
    if api_key in settings.api_keys:
        return
        
    # Check database API keys
    if api_key:
        api_key_obj = await crud.validate_api_key(db, api_key)
        if api_key_obj:
            return
    
    # If we get here, authentication failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid API Key or JWT Token"
    )

# --- Lifetime Management ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing application")
    
    # Initialize HTTP client for Ollama
    app.state.http_client = httpx.AsyncClient(
        base_url=settings.ollama_url,
        timeout=30,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
    )
    
    # Create uploads directory if it doesn't exist
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        # Continue startup even if DB init fails to allow for troubleshooting
    
    # Start security monitoring service
    try:
        from auth.security_monitor import start_security_monitoring
        start_security_monitoring()
        logger.info("Security monitoring service started")
    except Exception as e:
        logger.error(f"Failed to start security monitoring: {str(e)}")
    
    # Initialize cache manager
    try:
        from core.cache import cache_manager
        await cache_manager.initialize()
        logger.info("Cache manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize cache manager: {str(e)}")
    
    # Initialize job queue manager
    try:
        from core.job_queue import job_manager
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
        job_manager.redis_url = redis_url
        await job_manager.initialize()
        logger.info("Job queue manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize job queue manager: {str(e)}")
    
    yield
    
    logger.info("Shutting down application")
    
    # Shutdown cache manager
    try:
        from core.cache import cache_manager
        await cache_manager.shutdown()
        logger.info("Cache manager shutdown")
    except Exception as e:
        logger.error(f"Error shutting down cache manager: {str(e)}")
    
    # Shutdown job queue manager
    try:
        from core.job_queue import job_manager
        await job_manager.shutdown()
        logger.info("Job queue manager shutdown")
    except Exception as e:
        logger.error(f"Error shutting down job queue manager: {str(e)}")
    
    await app.state.http_client.aclose()

# --- App Initialization ---
app = FastAPI(
    title="Enterprise Model Manager Portal",
    lifespan=lifespan
)

# Add CORS middleware with environment-based configuration
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,  # Production-ready CORS configuration
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key", "Authorization"],
    allow_credentials=True,
)

# Add GZip middleware
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Add Security middleware for production hardening
from security.security_middleware import SecurityMiddleware, PRODUCTION_SECURITY_CONFIG

if os.getenv("ENVIRONMENT", "development") == "production":
    app.add_middleware(SecurityMiddleware, config=PRODUCTION_SECURITY_CONFIG)
else:
    # Development configuration - more permissive
    dev_config = PRODUCTION_SECURITY_CONFIG.copy()
    dev_config["allow_automation"] = True
    app.add_middleware(SecurityMiddleware, config=dev_config)

# Add Compliance middleware for audit logging and security monitoring
from auth.compliance_middleware import ComplianceMiddleware, DEVELOPMENT_CONFIG, PRODUCTION_CONFIG

compliance_config = PRODUCTION_CONFIG if os.getenv("ENVIRONMENT", "development") == "production" else DEVELOPMENT_CONFIG
app.add_middleware(ComplianceMiddleware, config=compliance_config)

# --- Caching ---
model_cache = TTLCache(maxsize=100, ttl=settings.cache_ttl)

# --- Pydantic Models ---
class ModelInfo(BaseModel):
    id: str
    name: str
    size: Optional[str]
    status: Optional[str]
    running: bool = False
    metadata: Dict[str, Any] = {}

class AvailableModelsResponse(BaseModel):
    models: List[ModelInfo]
    cache_hit: bool

class AuditLog(BaseModel):
    timestamp: float
    endpoint: str
    params: dict
    response: dict

class StartStopRequest(BaseModel):
    model_id: str
    
class ChatRequest(BaseModel):
    model_id: str
    prompt: str
    system_prompt: Optional[str] = None
    options: Optional[Dict[str, Any]] = None
    stream: bool = False
    conversation_id: Optional[str] = None
    
class ConversationRequest(BaseModel):
    model_id: str
    title: str
    system_prompt: Optional[str] = None

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

# --- Core Functions ---
async def get_ollama_models(
    use_cache: bool = True,
    db: AsyncSession = Depends(get_db)
) -> List[ModelInfo]:
    # Try Redis cache first
    if use_cache:
        try:
            from core.cache import get_cached, CacheNamespaces
            cached_models = await get_cached(CacheNamespaces.MODELS, "ollama_models")
            if cached_models:
                logger.debug("Cache hit for models from Redis/Memory cache")
                return cached_models
        except Exception as e:
            logger.warning(f"Cache error, proceeding without cache: {e}")

    # Fallback to old TTL cache for compatibility
    cache_key = "ollama_models"
    if use_cache and cache_key in model_cache:
        logger.debug("Cache hit for models from TTL cache")
        return model_cache[cache_key]

    try:
        # Get models from Ollama
        client = app.state.http_client
        start_time = time.monotonic()
        
        response = await client.get("/api/tags")
        response.raise_for_status()
        
        logger.info("Fetched models from Ollama in %.2f seconds", time.monotonic() - start_time)

        # Get local models from database
        db_models = await crud.get_models(db, {"is_local": True})
        db_models_dict = {model.id: model for model in db_models}
        
        # Get external models from database
        external_models = await crud.get_models(db, {"is_local": False})

        # Process Ollama models and update database if needed
        ollama_models = []
        for model_data in response.json().get("models", []):
            model_id = model_data["name"]
            model_name = model_id.split(":")[0].title()
            model_size = f"{model_data.get('size', 0) / (1024**3):.2f} GB" if model_data.get('size') else None
            
            # Check if model exists in database
            if model_id in db_models_dict:
                db_model = db_models_dict[model_id]
                
                # Update model in database if needed
                if db_model.size != model_size:
                    await crud.update_model(db, model_id, {"size": model_size})
                
                # Use database data but update status from Ollama
                model_info = ModelInfo(
                    id=db_model.id,
                    name=db_model.name,
                    size=model_size,
                    status="available",  # From Ollama
                    running=False,  # We'll determine this later
                    metadata={"digest": model_data.get("digest"), **db_model.metadata} if db_model.metadata else {"digest": model_data.get("digest")}
                )
            else:
                # Model not in database, create a basic entry
                model_info = ModelInfo(
                    id=model_id,
                    name=model_name,
                    size=model_size,
                    status="available",
                    running=False,
                    metadata={"digest": model_data.get("digest")}
                )
                
                # Add to database
                await crud.create_model(db, {
                    "id": model_id,
                    "name": model_name,
                    "size": model_size,
                    "provider": "unknown",
                    "is_active": True,
                    "status": "inactive",
                    "description": f"Ollama model {model_id}",
                    "metadata": {"digest": model_data.get("digest")},
                    "context_window": 4096  # Default
                })
            
            ollama_models.append(model_info)
        
        # Add external models from database
        for model in external_models:
            model_info = ModelInfo(
                id=model.id,
                name=model.name,
                size=model.size,
                status=model.status,
                running=model.status == "running",
                metadata=model.metadata or {}
            )
            ollama_models.append(model_info)
        
        # Cache the results in both cache systems
        try:
            from core.cache import set_cached, CacheNamespaces
            await set_cached(CacheNamespaces.MODELS, "ollama_models", ollama_models, ttl=300)
        except Exception as e:
            logger.warning(f"Failed to cache models in Redis/Memory cache: {e}")
        
        model_cache[cache_key] = ollama_models
        return ollama_models

    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama API error: {e.response.status_code}")
        
        # If Ollama is unavailable, return models from database
        db_models = await crud.get_models(db)
        if db_models:
            logger.info("Returning models from database due to Ollama API error")
            return [
                ModelInfo(
                    id=model.id,
                    name=model.name,
                    size=model.size,
                    status="unknown" if model.is_local else model.status,
                    running=False if model.is_local else model.status == "running",
                    metadata=model.metadata or {}
                ) for model in db_models
            ]
        
        raise HTTPException(status_code=502, detail=f"Ollama API error: {e.response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Ollama connection error: {e}")
        
        # If Ollama is unavailable, return models from database
        db_models = await crud.get_models(db)
        if db_models:
            logger.info("Returning models from database due to Ollama connection error")
            return [
                ModelInfo(
                    id=model.id,
                    name=model.name,
                    size=model.size,
                    status="unknown" if model.is_local else model.status,
                    running=False if model.is_local else model.status == "running",
                    metadata=model.metadata or {}
                ) for model in db_models
            ]
        
        raise HTTPException(status_code=503, detail="Ollama service unavailable")

# --- Routers ---
models_router = APIRouter(prefix="/api/models", tags=["Models"])

@models_router.get(
    "/available",
    response_model=AvailableModelsResponse
)
async def list_available_models(
    use_cache: bool = True,
    db: AsyncSession = Depends(get_db)
):
    models = await get_ollama_models(use_cache, db)
    return AvailableModelsResponse(
        models=models,
        cache_hit="ollama_models" in model_cache
    )

@models_router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_model(
    req: StartStopRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get model from database
        db_model = await crud.get_model(db, req.model_id)
        
        if not db_model:
            raise HTTPException(status_code=404, detail=f"Model {req.model_id} not found")
        
        # For local models, make API call to Ollama to start the model
        client = app.state.http_client
        endpoint = "/api/generate"  # Ollama doesn't have a dedicated start endpoint, but this will load the model
        
        # Minimal prompt to initialize the model
        payload = {
            "model": req.model_id,
            "prompt": "Hello",
            "stream": False,
            "options": {
                "num_predict": 1  # Minimal token generation
            }
        }
        
        logger.info(f"Starting model {req.model_id}")
        response = await client.post(endpoint, json=payload)
        response.raise_for_status()
        
        # Update model status in database
        await crud.update_model(db, req.model_id, {"status": "running"})
        
        # Update model status in our cache if it exists
        cache_key = "ollama_models"
        if cache_key in model_cache:
            for cached_model in model_cache[cache_key]:
                if cached_model.id == req.model_id:
                    cached_model.status = "running"
                    cached_model.running = True
        
        return {
            "message": f"Model {req.model_id} started successfully",
            "model_id": req.model_id,
            "status": "running"
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"Error starting model {req.model_id}: {str(e)}")
        
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error from Ollama API: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Unexpected error starting model {req.model_id}: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start model: {str(e)}"
        )

@models_router.post("/stop", status_code=status.HTTP_202_ACCEPTED)
async def stop_model(
    req: StartStopRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get model from database
        db_model = await crud.get_model(db, req.model_id)
        
        if not db_model:
            raise HTTPException(status_code=404, detail=f"Model {req.model_id} not found")
        
        # Note: Ollama doesn't have a dedicated stop endpoint
        # In a real implementation, you might need to:
        # 1. Track which models are loaded in memory
        # 2. Use a system-level approach to unload models (if Ollama provides this)
        # 3. Use Ollama's APIs if they add this functionality in the future
        
        logger.info(f"Stopping model {req.model_id}")
        
        # Update model status in database
        await crud.update_model(db, req.model_id, {"status": "stopped"})
        
        # Update model status in our cache if it exists
        cache_key = "ollama_models"
        if cache_key in model_cache:
            for cached_model in model_cache[cache_key]:
                if cached_model.id == req.model_id:
                    cached_model.status = "stopped"
                    cached_model.running = False
        
        return {
            "message": f"Model {req.model_id} stopped successfully",
            "model_id": req.model_id,
            "status": "stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping model {req.model_id}: {str(e)}")
        
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to stop model: {str(e)}"
        )

@models_router.websocket("/ws")
async def model_updates_websocket(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()  # Just keep alive
    except Exception:
        manager.disconnect(websocket)

# Chat Router
chat_router = APIRouter(prefix="/api/chat", tags=["Chat"])

# Create a new conversation
@chat_router.post("/conversations")
async def create_conversation(
    req: ConversationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Check if model exists
        db_model = await crud.get_model(db, req.model_id)
        if not db_model:
            raise HTTPException(status_code=404, detail=f"Model {req.model_id} not found")
        
        # Create conversation
        conversation = await crud.create_conversation(
            db=db,
            model_id=req.model_id,
            title=req.title,
            system_prompt=req.system_prompt
        )
        
        # Add user to conversation
        await crud.add_user_to_conversation(db, conversation.id, current_user.id)
        
        return {
            "id": conversation.id,
            "title": conversation.title,
            "model_id": conversation.model_id,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "system_prompt": conversation.system_prompt
        }
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create conversation: {str(e)}"
        )

# Get conversation by ID
@chat_router.get("/conversations/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get conversation
        conversation = await crud.get_conversation(db, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Check if user has access to this conversation
        user_conversations = await crud.get_user_conversations(db, current_user.id)
        if conversation.id not in [c.id for c in user_conversations]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this conversation"
            )
        
        # Get messages
        messages = await crud.get_conversation_messages(db, conversation_id)
        
        # Get files for conversation
        files = await crud.get_conversation_files(db, conversation_id)
        
        return {
            "id": conversation.id,
            "title": conversation.title,
            "model_id": conversation.model_id,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "system_prompt": conversation.system_prompt,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "tokens": msg.tokens,
                    "cost": msg.cost,
                    "metadata": msg.metadata,
                    "user_id": msg.user_id
                } for msg in messages
            ],
            "files": [
                {
                    "id": file.id,
                    "filename": file.original_filename,
                    "content_type": file.content_type,
                    "size": file.size,
                    "created_at": file.created_at.isoformat(),
                    "is_public": file.is_public
                } for file in files
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get conversation: {str(e)}"
        )

# List conversations for the user
@chat_router.get("/conversations")
async def list_conversations(
    model_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get conversations
        conversations = await crud.get_user_conversations(db, current_user.id, model_id)
        
        return {
            "conversations": [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "model_id": conv.model_id,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": len(conv.messages) if hasattr(conv, "messages") else 0
                } for conv in conversations
            ]
        }
    except Exception as e:
        logger.error(f"Error listing conversations: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list conversations: {str(e)}"
        )

# Update the chat completions endpoint to support conversations
@chat_router.post("/completions")
async def chat_completions(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        # Get model from database
        db_model = await crud.get_model(db, req.model_id)
        
        if not db_model:
            raise HTTPException(status_code=404, detail=f"Model {req.model_id} not found")
        
        start_time = time.monotonic()
        
        # Handle conversation
        conversation = None
        if req.conversation_id:
            conversation = await crud.get_conversation(db, req.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            # Check if user has access to this conversation
            user_conversations = await crud.get_user_conversations(db, current_user.id)
            if conversation.id not in [c.id for c in user_conversations]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this conversation"
                )
        
        # Local model (Ollama)
        client = app.state.http_client
        endpoint = "/api/chat" if "chat" in db_model.id.lower() else "/api/generate"
        
        # Prepare the payload
        if endpoint == "/api/chat":
            # Ollama chat endpoint format
            payload = {
                "model": req.model_id,
                "messages": [
                    {"role": "system", "content": req.system_prompt} if req.system_prompt else None,
                    {"role": "user", "content": req.prompt}
                ],
                "stream": req.stream
            }
            # Remove None values from messages
            payload["messages"] = [msg for msg in payload["messages"] if msg]
            
            # Add any additional options
            if req.options:
                payload["options"] = req.options
                
        else:
            # Ollama generation endpoint format
            prompt = req.prompt
            if req.system_prompt:
                prompt = f"{req.system_prompt}\n\n{prompt}"
                
            payload = {
                "model": req.model_id,
                "prompt": prompt,
                "stream": req.stream
            }
            
            # Add any additional options
            if req.options:
                payload["options"] = req.options
        
        # Make the request to Ollama
        response = await client.post(endpoint, json=payload)
        response.raise_for_status()
        response_data = response.json()
        
        # Extract the response based on endpoint type
        if endpoint == "/api/chat":
            content = response_data.get("message", {}).get("content", "")
        else:
            content = response_data.get("response", "")
        
        # Get token usage if available
        prompt_tokens = response_data.get("prompt_eval_count", 0)
        completion_tokens = response_data.get("eval_count", 0)
        total_tokens = prompt_tokens + completion_tokens
        
        processing_time = time.monotonic() - start_time
        
        # Calculate cost based on model rates (simplified)
        # In a real implementation, you would have different rates for different models and token types
        prompt_cost = prompt_tokens * 0.00001  # $0.01 per 1000 tokens
        completion_cost = completion_tokens * 0.00002  # $0.02 per 1000 tokens
        total_cost = prompt_cost + completion_cost
        
        # Store messages if conversation is provided
        if conversation:
            # Store user message
            user_message = await crud.add_message(
                db=db,
                conversation_id=conversation.id,
                role="user",
                content=req.prompt,
                user_id=current_user.id,
                tokens=prompt_tokens,
                cost=prompt_cost
            )
            
            # Store assistant message
            assistant_message = await crud.add_message(
                db=db,
                conversation_id=conversation.id,
                role="assistant",
                content=content,
                tokens=completion_tokens,
                cost=completion_cost
            )
        
        logger.info(f"Chat completion successful with model {req.model_id} in {processing_time:.2f}s")
        
        # Return the formatted response
        return {
            "id": str(uuid.uuid4()),
            "model": req.model_id,
            "created": int(time.time()),
            "content": content,
            "processing_time": processing_time,
            "usage": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "prompt_cost": prompt_cost,
                "completion_cost": completion_cost,
                "total_cost": total_cost
            },
            "conversation_id": conversation.id if conversation else None
        }
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama API error during chat: {e.response.status_code}")
        
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"Error from Ollama API: {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Unexpected error during chat: {str(e)}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Chat completion failed: {str(e)}"
        )

# Include routers
app.include_router(models_router)
app.include_router(chat_router)
app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(rbac_router)
app.include_router(workspace_router)
app.include_router(invitation_router)
app.include_router(compliance_router)
app.include_router(files_router)
# app.include_router(pipeline_router)  # Temporarily disabled
app.include_router(model_search_router)
app.include_router(analytics_router)
app.include_router(cache_management_router)
# app.include_router(job_management_router)  # Temporarily disabled
app.include_router(streaming_chat_router)
app.include_router(conversation_management_router)
app.include_router(message_export_router)
app.include_router(websocket_router)
# app.include_router(pipeline_execution_router)  # Temporarily disabled
app.include_router(help_system_router)

# GitHub integration router
from integrations.github_router import router as github_router
app.include_router(github_router)

# Health Check
@app.get("/health", include_in_schema=False)
async def health_check():
    try:
        response = await app.state.http_client.get("/")
        return {"status": "healthy", "ollama_status": response.status_code}
    except Exception as e:
        return {"status": "degraded", "error": str(e)}

# Audit Middleware
@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    logger.info(
        "API request processed",
        extra={
            "path": request.url.path,
            "method": request.method,
            "duration": process_time,
            "status_code": response.status_code
        }
    )
    return response

# Startup Entry
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        access_log=True,
        proxy_headers=True,
        timeout_keep_alive=30
    )