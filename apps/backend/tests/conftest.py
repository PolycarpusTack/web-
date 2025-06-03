import asyncio
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from faker import Faker
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock

# Import Base from our own definition instead of from db.database
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# Import model definitions directly
from db.models import User, APIKey, Model, Tag, Conversation, Message, File, MessageFile, MessageThread

# Import our application
from main import app
from db.database import get_db
from auth.jwt import create_access_token

# Test database URL - use in-memory database
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create engine for tests
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool  # Use NullPool to avoid engine caching issues during tests
)

# Create session factory
test_async_session_maker = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

# Initialize faker for test data generation
fake = Faker()


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_engine():
    """Creates a test database engine for each test."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield test_engine

    # Close engine
    await test_engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def db_session(db_engine):
    """Creates a test database session for each test."""
    async with test_async_session_maker() as session:
        yield session
        # Always roll back after tests to avoid test side effects
        await session.rollback()
        await session.close()


@pytest_asyncio.fixture(scope="function")
async def test_user(db_session):
    """Creates a test user."""
    from db.crud import create_user
    from auth.password import get_password_hash

    hashed_password = get_password_hash("testpassword")
    user = await create_user(
        db=db_session,
        username=f"testuser_{fake.uuid4()}",
        email=fake.email(),
        hashed_password=hashed_password,
        full_name=fake.name()
    )
    return user


@pytest_asyncio.fixture(scope="function")
async def test_api_key(db_session, test_user):
    """Creates a test API key."""
    from db.crud import create_api_key
    import secrets

    api_key = await create_api_key(
        db=db_session,
        user_id=test_user.id,
        key=secrets.token_urlsafe(32),
        name="Test API Key"
    )
    return api_key


@pytest_asyncio.fixture(scope="function")
async def test_model(db_session):
    """Creates a test model."""
    from db.crud import create_model

    model_data = {
        "id": f"test-model-{fake.uuid4()}",
        "name": "Test Model",
        "provider": "test",
        "description": "Test model for unit tests",
        "version": "1.0",
        "is_active": True,
        "context_window": 4096
    }
    model = await create_model(db=db_session, model_data=model_data)
    return model


@pytest_asyncio.fixture(scope="function")
async def test_conversation(db_session, test_model, test_user):
    """Creates a test conversation."""
    from db.crud import create_conversation, add_user_to_conversation

    conversation = await create_conversation(
        db=db_session,
        model_id=test_model.id,
        title=f"Test Conversation {fake.uuid4()}",
        system_prompt="This is a test conversation."
    )

    # Add user to conversation
    await add_user_to_conversation(db_session, conversation.id, test_user.id)

    return conversation


@pytest_asyncio.fixture(scope="function")
async def test_message(db_session, test_conversation, test_user):
    """Creates a test message."""
    from db.crud import add_message

    message = await add_message(
        db=db_session,
        conversation_id=test_conversation.id,
        role="user",
        content=fake.paragraph(),
        user_id=test_user.id
    )
    return message


@pytest_asyncio.fixture(scope="function")
async def test_thread(db_session, test_conversation, test_user):
    """Creates a test message thread."""
    thread = MessageThread(
        conversation_id=test_conversation.id,
        title=f"Test Thread {fake.uuid4()}",
        creator_id=test_user.id
    )
    db_session.add(thread)
    await db_session.commit()
    await db_session.refresh(thread)
    return thread


@pytest_asyncio.fixture(scope="function")
async def test_file(db_session, test_user, test_conversation):
    """Creates a test file."""
    from db.crud import create_file

    file = await create_file(
        db=db_session,
        filename=f"test-{fake.uuid4()}.txt",
        original_filename="test.txt",
        content_type="text/plain",
        size=100,
        path=f"/tmp/test-{fake.uuid4()}.txt",
        user_id=test_user.id,
        conversation_id=test_conversation.id
    )
    return file


# Test client fixtures

@pytest.fixture
async def client(db_session):
    """Create async test client with database dependency override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Use httpx AsyncClient for async testing
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
def sync_client(db_session):
    """Create synchronous test client for simple tests."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Clean up dependency overrides
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(test_user):
    """Create authentication headers with JWT token."""
    access_token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def api_key_headers(test_api_key):
    """Create authentication headers with API key."""
    return {"X-API-Key": test_api_key.key}


# Mock fixtures

@pytest.fixture
def mock_ollama():
    """Mock all Ollama API requests."""
    from tests.mocks.ollama_mock import mock_ollama_request
    
    with patch('httpx.AsyncClient.request', side_effect=mock_ollama_request) as mock:
        yield mock


@pytest.fixture
def mock_external_apis():
    """Mock all external API calls."""
    with patch('httpx.AsyncClient.get') as mock_get, \
         patch('httpx.AsyncClient.post') as mock_post:
        
        # Configure default responses
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {"status": "ok"}
        
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "ok"}
        
        yield {"get": mock_get, "post": mock_post}