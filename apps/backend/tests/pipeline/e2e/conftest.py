"""
End-to-End test configuration for Code Factory Pipeline tests.

This module contains fixtures for setting up an E2E test environment
including a running FastAPI application with a test database.
"""

import os
import pytest
import asyncio
import httpx
import sys
from typing import AsyncGenerator, Dict, Any, Generator
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from asgi_lifespan import LifespanManager

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))

from db.database import Base, get_db
from db.init_db import init_db
from auth.jwt import create_access_token


# Test database URL
TEST_SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test_pipeline.db"

# Create test engine and session
engine = create_async_engine(
    TEST_SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=NullPool
)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# Override get_db in FastAPI dependency injection
async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to override the database session with a test session."""
    async with TestingSessionLocal() as session:
        yield session


# Authentication helper functions
def get_authorization_header(user_id: str = "test-user") -> Dict[str, str]:
    """Create a JWT token and return it as an authorization header."""
    access_token = create_access_token(
        data={"sub": user_id, "role": "admin"}
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_app() -> AsyncGenerator[FastAPI, None]:
    """Create a test FastAPI app with test database."""
    # Import main app here to avoid circular imports
    from main import app
    
    # Override the database dependency for testing
    app.dependency_overrides[get_db] = override_get_db
    
    async with LifespanManager(app):
        yield app


@pytest.fixture(scope="session")
async def test_db() -> AsyncGenerator[None, None]:
    """Set up test database with all tables."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize database with test data
    async with TestingSessionLocal() as session:
        await init_db(session, test_mode=True)
    
    yield
    
    # Clean up database after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="session")
async def test_client(test_app: FastAPI, test_db: None) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Create a test client for the FastAPI app."""
    async with httpx.AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def auth_headers() -> Dict[str, str]:
    """Create authentication headers for test requests."""
    return get_authorization_header()


@pytest.fixture
async def sample_pipeline(test_client: httpx.AsyncClient, auth_headers: Dict[str, str]) -> Dict[str, Any]:
    """Create a sample pipeline for testing."""
    # Create a simple pipeline with one prompt step
    pipeline_data = {
        "name": "Test Pipeline",
        "description": "A test pipeline for e2e tests",
        "is_public": True,
        "tags": ["test", "e2e"]
    }
    
    # Create the pipeline
    response = await test_client.post(
        "/api/pipelines",
        json=pipeline_data,
        headers=auth_headers
    )
    
    pipeline = response.json()
    
    # Add a prompt step to the pipeline
    step_data = {
        "name": "Test Prompt",
        "type": "prompt",
        "order": 0,
        "config": {
            "model_id": "ollama/mistral:7b-instruct",
            "prompt": "Say hello!",
            "system_prompt": "You are a helpful assistant."
        }
    }
    
    await test_client.post(
        f"/api/pipelines/{pipeline['id']}/steps",
        json=step_data,
        headers=auth_headers
    )
    
    return pipeline