"""
Global test configuration for Web+ backend.

This module provides comprehensive test fixtures and configuration
to ensure reliable, isolated, and fast test execution.
"""
import asyncio
import pytest
import pytest_asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy import event
from unittest.mock import AsyncMock, MagicMock

# Import our application components with error handling
try:
    from main import app
    from db.database import get_db, Base
    from db.models import User, Model, Conversation, Message
    from auth.password import get_password_hash
    from auth.jwt import create_access_token
except ImportError as e:
    print(f"Warning: Could not import some modules: {e}")
    # Create mock objects for basic testing
    app = None
    get_db = None
    Base = None
    User = None
    
# Import APIKey separately as it may be in a different module
try:
    from db.models import APIKey
except ImportError:
    try:
        from auth.api_keys import APIKey
    except ImportError:
        APIKey = None
    get_password_hash = lambda x: f"hashed_{x}"
    create_access_token = lambda x: f"token_{x}"

# Test database URL - use in-memory SQLite for speed
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine with specific configuration for testing
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Set to True for SQL debugging
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
        "cache": "shared",  # Enable shared cache for better performance
    },
)


@pytest_asyncio.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.
    
    This fixture:
    1. Creates all tables
    2. Provides a clean session
    3. Rolls back all changes after the test
    4. Drops all tables for cleanup
    """
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session
    async with AsyncSession(test_engine, expire_on_commit=False) as session:
        yield session
    
    # Cleanup: drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an HTTP client for testing API endpoints.
    
    This fixture:
    1. Overrides the database dependency
    2. Provides an async HTTP client
    3. Handles app lifecycle management
    """
    # Override the database dependency
    app.dependency_overrides[get_db] = lambda: db_session
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    # Clear dependency overrides
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user for authentication tests."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
        is_superuser=False,
        role="user"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user for administrative tests."""
    user = User(
        username="adminuser",
        email="admin@example.com",
        hashed_password=get_password_hash("adminpassword123"),
        full_name="Admin User",
        is_active=True,
        is_verified=True,
        is_superuser=True,
        role="admin"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def user_token(test_user: User) -> str:
    """Create a JWT token for the test user."""
    return create_access_token(data={"sub": test_user.username})


@pytest_asyncio.fixture
async def admin_token(admin_user: User) -> str:
    """Create a JWT token for the admin user."""
    return create_access_token(data={"sub": admin_user.username})


@pytest_asyncio.fixture
async def authenticated_client(client: AsyncClient, user_token: str) -> AsyncClient:
    """Create an authenticated HTTP client."""
    client.headers.update({"Authorization": f"Bearer {user_token}"})
    return client


@pytest_asyncio.fixture
async def admin_client(client: AsyncClient, admin_token: str) -> AsyncClient:
    """Create an admin authenticated HTTP client."""
    client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return client


# @pytest_asyncio.fixture
# async def test_api_key(db_session: AsyncSession, test_user: User) -> APIKey:
#     """Create a test API key."""
#     api_key = APIKey(
#         key="test_api_key_12345",
#         name="Test API Key",
#         user_id=test_user.id,
#         is_active=True
#     )
#     db_session.add(api_key)
#     await db_session.commit()
#     await db_session.refresh(api_key)
#     return api_key


@pytest_asyncio.fixture
async def test_model(db_session: AsyncSession) -> Model:
    """Create a test AI model."""
    model = Model(
        id="test-model",
        name="Test Model",
        provider="test",
        description="A test model for unit testing",
        version="1.0",
        is_active=True,
        context_window=4096,
        max_output_tokens=2048
    )
    db_session.add(model)
    await db_session.commit()
    await db_session.refresh(model)
    return model


@pytest_asyncio.fixture
async def test_conversation(db_session: AsyncSession, test_user: User, test_model: Model) -> Conversation:
    """Create a test conversation."""
    conversation = Conversation(
        id="test-conversation-id",
        title="Test Conversation",
        model_id=test_model.id,
        system_prompt="You are a helpful test assistant.",
        user_id=test_user.id
    )
    db_session.add(conversation)
    await db_session.commit()
    await db_session.refresh(conversation)
    return conversation


@pytest_asyncio.fixture
async def test_messages(db_session: AsyncSession, test_conversation: Conversation, test_user: User):
    """Create test messages in a conversation."""
    messages = [
        Message(
            id="msg-1",
            conversation_id=test_conversation.id,
            role="user",
            content="Hello, this is a test message.",
            user_id=test_user.id,
            tokens=10,
            cost=0.001
        ),
        Message(
            id="msg-2",
            conversation_id=test_conversation.id,
            role="assistant",
            content="Hello! I'm here to help with your test.",
            tokens=15,
            cost=0.002
        )
    ]
    
    for message in messages:
        db_session.add(message)
    
    await db_session.commit()
    
    for message in messages:
        await db_session.refresh(message)
    
    return messages


@pytest.fixture
def mock_ollama_client():
    """Mock the Ollama HTTP client for testing."""
    mock_client = AsyncMock()
    
    # Mock successful model list response
    mock_client.get.return_value.json.return_value = {
        "models": [
            {
                "name": "test-model:latest",
                "size": 1000000,
                "digest": "test-digest-123"
            }
        ]
    }
    
    # Mock successful chat completion
    mock_client.post.return_value.json.return_value = {
        "message": {"content": "Test response from mock"},
        "done": True,
        "total_duration": 1000000,
        "prompt_eval_count": 10,
        "eval_count": 15
    }
    
    return mock_client


@pytest.fixture
def mock_file_system(tmp_path):
    """Create a temporary file system for file operation tests."""
    # Create test directories
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    
    temp_dir = tmp_path / "temp"
    temp_dir.mkdir()
    
    return {
        "upload_dir": upload_dir,
        "temp_dir": temp_dir,
        "base_path": tmp_path
    }


# Pytest configuration for better test output
def pytest_configure(config):
    """Configure pytest with custom markers and settings."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow (requires --slow flag)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )


def pytest_runtest_setup(item):
    """Setup function run before each test."""
    # Skip slow tests unless explicitly requested
    if "slow" in item.keywords and not item.config.getoption("--slow", default=False):
        pytest.skip("Slow test skipped (use --slow flag to run)")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--slow",
        action="store_true",
        default=False,
        help="Run slow tests"
    )
    parser.addoption(
        "--integration",
        action="store_true", 
        default=False,
        help="Run integration tests"
    )


# Async test helpers
class AsyncContextManager:
    """Helper class for async context management in tests."""
    
    def __init__(self, async_func):
        self.async_func = async_func
        
    async def __aenter__(self):
        return await self.async_func()
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


# Performance testing utilities
class PerformanceTracker:
    """Track performance metrics during tests."""
    
    def __init__(self):
        self.metrics = {}
    
    def start_timer(self, name: str):
        import time
        self.metrics[name] = {"start": time.time()}
    
    def end_timer(self, name: str):
        import time
        if name in self.metrics:
            self.metrics[name]["end"] = time.time()
            self.metrics[name]["duration"] = self.metrics[name]["end"] - self.metrics[name]["start"]
    
    def get_duration(self, name: str) -> float:
        return self.metrics.get(name, {}).get("duration", 0.0)


@pytest.fixture
def performance_tracker():
    """Provide a performance tracker for test timing."""
    return PerformanceTracker()


# Memory usage tracking for performance tests
@pytest.fixture
def memory_tracker():
    """Track memory usage during tests."""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    
    class MemoryTracker:
        def __init__(self):
            self.start_memory = process.memory_info().rss
        
        def current_usage(self):
            return process.memory_info().rss
        
        def delta(self):
            return self.current_usage() - self.start_memory
        
        def delta_mb(self):
            return self.delta() / (1024 * 1024)
    
    return MemoryTracker()