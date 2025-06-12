"""
Minimal FastAPI app to test the models endpoint
"""
from fastapi import FastAPI, HTTPException
import httpx
import asyncio
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI()

# Global HTTP client
http_client = httpx.AsyncClient(
    base_url="http://localhost:11434",
    timeout=30
)

@app.get("/test/models")
async def test_models():
    try:
        logger.info("Fetching models from Ollama...")
        response = await http_client.get("/api/tags")
        response.raise_for_status()
        
        data = response.json()
        models = data.get("models", [])
        
        return {
            "status": "success",
            "models_count": len(models),
            "models": [{"name": m["name"], "size": m.get("size")} for m in models[:3]]
        }
    except httpx.HTTPError as e:
        logger.error(f"HTTP error: {e}")
        raise HTTPException(status_code=502, detail=f"Ollama error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("shutdown")
async def shutdown():
    await http_client.aclose()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
