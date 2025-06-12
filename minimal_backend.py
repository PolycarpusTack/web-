"""
Minimal backend to test models endpoint
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List, Dict, Any
import httpx
import logging
import os
import sys

# Add backend modules to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps", "backend"))

from db.database import get_db
from db import crud

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Models
class ModelInfo(BaseModel):
    id: str
    name: str
    size: str
    status: str
    running: bool
    metadata: Dict[str, Any] = {}

class AvailableModelsResponse(BaseModel):
    models: List[ModelInfo]
    cache_hit: bool = False

# Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize HTTP client
    app.state.http_client = httpx.AsyncClient(
        base_url="http://localhost:11434",
        timeout=30
    )
    logger.info("HTTP client initialized")
    
    yield
    
    # Cleanup
    await app.state.http_client.aclose()
    logger.info("HTTP client closed")

# Create app
app = FastAPI(lifespan=lifespan)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/models/available", response_model=AvailableModelsResponse)
async def get_models(db: AsyncSession = Depends(get_db)):
    try:
        # Get models from Ollama
        client = app.state.http_client
        response = await client.get("/api/tags")
        response.raise_for_status()
        
        ollama_data = response.json()
        models = []
        
        for model_data in ollama_data.get("models", []):
            model_id = model_data["name"]
            model_name = model_id.split(":")[0].title()
            model_size = f"{model_data.get('size', 0) / (1024**3):.2f} GB" if model_data.get('size') else "Unknown"
            
            models.append(ModelInfo(
                id=model_id,
                name=model_name,
                size=model_size,
                status="available",
                running=False,
                metadata={"digest": model_data.get("digest", "")}
            ))
        
        # Add models from database
        db_models = await crud.get_models(db, {"is_local": False})
        for db_model in db_models:
            models.append(ModelInfo(
                id=db_model.id,
                name=db_model.name,
                size=db_model.size or "Unknown",
                status=db_model.status,
                running=db_model.status == "running",
                metadata=db_model.model_metadata or {}
            ))
        
        return AvailableModelsResponse(models=models, cache_hit=False)
        
    except httpx.HTTPError as e:
        logger.error(f"Ollama error: {e}")
        raise HTTPException(status_code=502, detail=f"Ollama service error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
