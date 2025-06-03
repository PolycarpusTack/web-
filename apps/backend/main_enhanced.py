"""
Enhanced main.py with proper CORS, logging, and WebSocket support
"""
from fastapi import FastAPI, WebSocket, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import httpx
import logging
import os

# Import our enhanced modules
from core.config import settings
from core.middleware import setup_middleware
from core.websocket import manager, websocket_endpoint

# Database imports
from db.database import init_async_db, close_async_db
from db.init_db import init_db

# Router imports
from auth.router import router as auth_router
from auth.api_keys import router as api_keys_router
from files.router import router as files_router
from pipeline.router import router as pipeline_router

# Model router
from routers.models import router as models_router
from routers.chat import router as chat_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("Starting Web+ Backend")
    
    # Initialize HTTP client for Ollama
    app.state.http_client = httpx.AsyncClient(
        base_url=settings.ollama_url,
        timeout=httpx.Timeout(settings.ollama_timeout),
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
    )
    
    # Create directories
    os.makedirs(settings.upload_dir, exist_ok=True)
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Continue startup for development
    
    yield
    
    # Cleanup
    logger.info("Shutting down Web+ Backend")
    await app.state.http_client.aclose()
    await close_async_db()


# Create FastAPI app
app = FastAPI(
    title="Web+ Backend API",
    description="Backend API for Web+ platform",
    version=settings.app_version,
    lifespan=lifespan,
    debug=settings.debug,
)

# Configure CORS with proper settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
    expose_headers=settings.cors_expose_headers,
)

# Add compression
app.add_middleware(GZipMiddleware, minimum_size=1024)

# Setup custom middleware
setup_middleware(app, settings)

# Include routers
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(api_keys_router, prefix="/api/keys", tags=["API Keys"])
app.include_router(models_router, prefix="/api/models", tags=["Models"])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"])
app.include_router(files_router, prefix="/api/files", tags=["Files"])
app.include_router(pipeline_router, prefix="/api/pipelines", tags=["Pipelines"])

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Ollama connection
        ollama_status = "unknown"
        try:
            response = await app.state.http_client.get("/")
            ollama_status = "healthy" if response.status_code == 200 else "degraded"
        except:
            ollama_status = "unavailable"
        
        return {
            "status": "healthy",
            "version": settings.app_version,
            "services": {
                "database": "healthy",  # TODO: Add actual DB check
                "ollama": ollama_status,
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e),
            "version": settings.app_version,
        }

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint_handler(
    websocket: WebSocket,
    token: str = None,
    api_key: str = None
):
    """
    WebSocket endpoint for real-time updates
    Supports both JWT token and API key authentication
    """
    # TODO: Add authentication validation
    user_id = None
    
    if token:
        # Validate JWT token
        # user_id = validate_jwt_token(token)
        pass
    elif api_key:
        # Validate API key
        # user_id = validate_api_key(api_key)
        pass
    
    await websocket_endpoint(websocket, user_id)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
    }

# WebSocket stats endpoint (for monitoring)
@app.get("/api/ws/stats")
async def websocket_stats():
    """Get WebSocket connection statistics"""
    return manager.get_stats()

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main_enhanced:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        workers=1 if settings.debug else settings.workers,
        log_level=settings.log_level.lower(),
        access_log=True,
    )