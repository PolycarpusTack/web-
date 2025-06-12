"""
Debug why the backend is shutting down immediately
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "apps", "backend"))

from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def test_lifespan(app: FastAPI):
    logger.info("Lifespan: Starting up...")
    yield
    logger.info("Lifespan: Shutting down...")

app = FastAPI(lifespan=test_lifespan)

@app.get("/test")
async def test():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn...")
    uvicorn.run(app, host="0.0.0.0", port=8006)
