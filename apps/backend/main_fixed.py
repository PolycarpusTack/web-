"""
Full Web+ Backend - Fixed Version
"""
import os
import sys
import logging
import asyncio

# Force the backend directory into Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Now we can import our modules
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import httpx
import uvicorn

# Import our modules
from db.database import get_db, init_async_db
from db.init_db import init_db
from sqlalchemy.ext.asyncio import AsyncSession
from core.config import settings

# Import routers
from auth.router import router as auth_router
from auth.api_keys import router as api_keys_router
from auth.rbac_router import router as rbac_router
from auth.workspace_router import router as workspace_router
from auth.invitation_router import router as invitation_router
from auth.compliance_router import router as compliance_router
from files.router import router as files_router
from api.model_search import router as model_search_router
from api.model_analytics import router as analytics_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import main app components
from main import (
    get_ollama_models, 
    models_router,
    conversation_router,
    streaming_router,
    pipeline_analysis_router,
    message_export_router,
    limiter,
    _rate_limit_exceeded_handler,
    RateLimitExceeded
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    try:
        logger.info("Starting Web+ Backend...")
        
        # Initialize HTTP client for Ollama
        app.state.http_client = httpx.AsyncClient(
            base_url=settings.ollama_url,
            timeout=30,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
        logger.info("HTTP client initialized")
        
        # Create uploads directory
        os.makedirs(settings.upload_dir, exist_ok=True)
        logger.info(f"Upload directory ready: {settings.upload_dir}")
        
        # Initialize database
        try:
            logger.info("Initializing database...")
            await init_db()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            # Continue anyway for now
        
        # Initialize cache (optional)
        try:
            from core.cache import cache_manager
            await cache_manager.initialize()
            logger.info("Cache initialized")
        except Exception as e:
            logger.warning(f"Cache initialization failed (non-critical): {e}")
        
        # Initialize job queue (optional)
        try:
            from core.job_queue import job_manager
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/1")
            job_manager.redis_url = redis_url
            await job_manager.initialize()
            logger.info("Job queue initialized")
        except Exception as e:
            logger.warning(f"Job queue initialization failed (non-critical): {e}")
        
        logger.info("✅ Web+ Backend startup complete!")
        
        yield  # This is where the app runs
        
        # Shutdown
        logger.info("Shutting down Web+ Backend...")
        
        # Cleanup
        await app.state.http_client.aclose()
        
        try:
            from core.cache import cache_manager
            await cache_manager.shutdown()
        except:
            pass
            
        try:
            from core.job_queue import job_manager
            await job_manager.shutdown()
        except:
            pass
            
    except Exception as e:
        logger.error(f"Fatal startup error: {e}")
        raise

# Create FastAPI app
app = FastAPI(
    title="Web+ Backend",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Include all routers
app.include_router(auth_router)
app.include_router(api_keys_router)
app.include_router(rbac_router)
app.include_router(workspace_router)
app.include_router(invitation_router)
app.include_router(compliance_router)
app.include_router(files_router)
app.include_router(models_router)
app.include_router(conversation_router)
app.include_router(streaming_router)
app.include_router(pipeline_analysis_router)
app.include_router(message_export_router)
app.include_router(model_search_router)
app.include_router(analytics_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Web+ Backend",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    logger.info("Starting Web+ Backend on port 8002...")
    uvicorn.run(
        "main_fixed:app",
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )
