"""
Core functionality tests for Web+ backend.

These tests validate the essential components that make our Ferrari run.
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

try:
    from db.models import User, Model, Conversation, Message, Pipeline, PipelineStep
    from db.crud import create_user, get_user_by_username, create_model
except ImportError:
    # Mock objects for testing when modules aren't available
    User = Model = Conversation = Message = Pipeline = PipelineStep = None
    create_user = get_user_by_username = create_model = None


@pytest.mark.unit
class TestDatabaseConnectivity:
    """Test database connection and basic operations."""
    
    async def test_database_session_creation(self, db_session: AsyncSession):
        """Test that we can create a database session."""
        assert db_session is not None
        
        # Test a simple query
        result = await db_session.execute("SELECT 1")
        assert result.scalar() == 1
    
    async def test_user_creation_and_retrieval(self, db_session: AsyncSession):
        """Test user CRUD operations."""
        # Create a user
        user_data = {
            "username": "testuser123",
            "email": "test123@example.com",
            "password": "testpassword",
            "full_name": "Test User"
        }
        
        user = await create_user(db_session, user_data)
        assert user.username == "testuser123"
        assert user.email == "test123@example.com"
        assert user.is_active is True
        
        # Retrieve the user
        retrieved_user = await get_user_by_username(db_session, "testuser123")
        assert retrieved_user is not None
        assert retrieved_user.id == user.id


@pytest.mark.unit
class TestAPIEndpoints:
    """Test critical API endpoints."""
    
    async def test_health_check(self, client: AsyncClient):
        """Test the health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
    
    async def test_authentication_flow(self, client: AsyncClient):
        """Test user registration and login."""
        # Register a new user
        register_data = {
            "username": "newuser",
            "email": "newuser@example.com", 
            "password": "password123",
            "full_name": "New User"
        }
        
        response = await client.post("/auth/register", json=register_data)
        assert response.status_code == 201
        
        user_data = response.json()
        assert user_data["username"] == "newuser"
        assert "password" not in user_data  # Password should not be returned
        
        # Login with the new user
        login_data = {
            "username": "newuser",
            "password": "password123"
        }
        
        response = await client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        
        token_data = response.json()
        assert "access_token" in token_data
        assert token_data["token_type"] == "bearer"
    
    async def test_protected_endpoint_access(self, authenticated_client: AsyncClient):
        """Test accessing protected endpoints with authentication."""
        response = await authenticated_client.get("/auth/me")
        assert response.status_code == 200
        
        user_data = response.json()
        assert "username" in user_data
        assert "email" in user_data


@pytest.mark.unit
class TestModelManagement:
    """Test AI model management functionality."""
    
    async def test_model_creation(self, db_session: AsyncSession):
        """Test creating AI models."""
        model_data = {
            "id": "test-model-123",
            "name": "Test Model",
            "provider": "test_provider",
            "description": "A test model",
            "version": "1.0",
            "context_window": 4096,
            "max_output_tokens": 2048
        }
        
        model = await create_model(db_session, model_data)
        assert model.id == "test-model-123"
        assert model.name == "Test Model"
        assert model.is_active is True
    
    async def test_models_api_endpoint(self, authenticated_client: AsyncClient):
        """Test the models API endpoint."""
        # Note: This might return empty or mock data depending on setup
        response = await authenticated_client.get("/api/models/available")
        assert response.status_code == 200
        
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)


@pytest.mark.unit 
class TestConversationManagement:
    """Test conversation and message functionality."""
    
    async def test_conversation_creation(self, authenticated_client: AsyncClient, test_model: Model):
        """Test creating a conversation."""
        conversation_data = {
            "model_id": test_model.id,
            "title": "Test Conversation",
            "system_prompt": "You are a helpful assistant."
        }
        
        response = await authenticated_client.post("/api/chat/conversations", json=conversation_data)
        assert response.status_code == 200
        
        conversation = response.json()
        assert conversation["title"] == "Test Conversation"
        assert conversation["model_id"] == test_model.id
    
    async def test_conversation_listing(self, authenticated_client: AsyncClient):
        """Test listing conversations."""
        response = await authenticated_client.get("/api/chat/conversations")
        assert response.status_code == 200
        
        data = response.json()
        assert "conversations" in data
        assert isinstance(data["conversations"], list)


@pytest.mark.integration
class TestPipelineSystem:
    """Test the pipeline execution system."""
    
    async def test_pipeline_creation(self, authenticated_client: AsyncClient):
        """Test creating a pipeline."""
        pipeline_data = {
            "name": "Test Pipeline",
            "description": "A test pipeline for validation",
            "is_public": False,
            "tags": ["test"]
        }
        
        response = await authenticated_client.post("/api/pipelines", json=pipeline_data)
        assert response.status_code == 201
        
        pipeline = response.json()
        assert pipeline["name"] == "Test Pipeline"
        assert pipeline["is_active"] is True
    
    async def test_pipeline_step_creation(self, authenticated_client: AsyncClient):
        """Test adding steps to a pipeline."""
        # First create a pipeline
        pipeline_data = {
            "name": "Step Test Pipeline",
            "description": "For testing steps",
            "is_public": False
        }
        
        response = await authenticated_client.post("/api/pipelines", json=pipeline_data)
        assert response.status_code == 201
        pipeline = response.json()
        pipeline_id = pipeline["id"]
        
        # Add a step
        step_data = {
            "name": "Test Step",
            "type": "prompt",
            "order": 0,
            "config": {
                "model_id": "test-model",
                "prompt": "Hello, world!",
                "options": {"temperature": 0.7}
            },
            "description": "A test step"
        }
        
        response = await authenticated_client.post(f"/api/pipelines/{pipeline_id}/steps", json=step_data)
        assert response.status_code == 201
        
        step = response.json()
        assert step["name"] == "Test Step"
        assert step["type"] == "prompt"


@pytest.mark.performance
class TestPerformance:
    """Performance and load testing."""
    
    async def test_database_performance(self, db_session: AsyncSession, performance_tracker):
        """Test database operation performance."""
        performance_tracker.start_timer("user_creation")
        
        # Create multiple users to test bulk operations
        users = []
        for i in range(50):
            user_data = {
                "username": f"perfuser{i}",
                "email": f"perfuser{i}@example.com",
                "password": "password123",
                "full_name": f"Performance User {i}"
            }
            user = await create_user(db_session, user_data)
            users.append(user)
        
        performance_tracker.end_timer("user_creation")
        
        # Should create 50 users in reasonable time (under 5 seconds)
        duration = performance_tracker.get_duration("user_creation")
        assert duration < 5.0, f"User creation took too long: {duration}s"
        assert len(users) == 50
    
    async def test_api_response_time(self, authenticated_client: AsyncClient, performance_tracker):
        """Test API response times."""
        performance_tracker.start_timer("api_health_check")
        
        response = await authenticated_client.get("/health")
        
        performance_tracker.end_timer("api_health_check")
        
        # Health check should be very fast
        duration = performance_tracker.get_duration("api_health_check")
        assert response.status_code == 200
        assert duration < 1.0, f"Health check too slow: {duration}s"


@pytest.mark.security
class TestSecurity:
    """Security-focused tests."""
    
    async def test_password_hashing(self, db_session: AsyncSession):
        """Test that passwords are properly hashed."""
        user_data = {
            "username": "securitytest",
            "email": "security@example.com",
            "password": "plaintext_password",
            "full_name": "Security Test"
        }
        
        user = await create_user(db_session, user_data)
        
        # Password should be hashed, not stored as plaintext
        assert user.hashed_password != "plaintext_password"
        assert len(user.hashed_password) > 20  # Hashed passwords are longer
        assert user.hashed_password.startswith("$2b$")  # bcrypt hash format
    
    async def test_unauthorized_access(self, client: AsyncClient):
        """Test that protected endpoints reject unauthorized access."""
        response = await client.get("/auth/me")
        assert response.status_code == 401
        
        response = await client.get("/api/chat/conversations")
        assert response.status_code == 401
    
    async def test_sql_injection_protection(self, authenticated_client: AsyncClient):
        """Test protection against SQL injection attacks."""
        # Try SQL injection in search parameters
        malicious_input = "'; DROP TABLE users; --"
        
        response = await authenticated_client.get(f"/api/models/available?search={malicious_input}")
        
        # Should not crash and should return proper response
        assert response.status_code in [200, 400]  # Either works or rejects safely
        
        # Database should still be functional after the attempt
        response2 = await authenticated_client.get("/auth/me")
        assert response2.status_code == 200


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    async def test_invalid_json_handling(self, client: AsyncClient):
        """Test handling of invalid JSON in requests."""
        response = await client.post(
            "/auth/register",
            data="invalid json data",
            headers={"Content-Type": "application/json"}
        )
        
        # Should return proper error code for malformed JSON
        assert response.status_code == 422
    
    async def test_missing_required_fields(self, client: AsyncClient):
        """Test handling of missing required fields."""
        incomplete_data = {
            "username": "incomplete_user"
            # Missing email, password, etc.
        }
        
        response = await client.post("/auth/register", json=incomplete_data)
        assert response.status_code == 422
        
        error_data = response.json()
        assert "detail" in error_data
    
    async def test_duplicate_user_creation(self, client: AsyncClient):
        """Test handling of duplicate user creation."""
        user_data = {
            "username": "duplicate_user",
            "email": "duplicate@example.com",
            "password": "password123",
            "full_name": "Duplicate User"
        }
        
        # Create user first time - should succeed
        response1 = await client.post("/auth/register", json=user_data)
        assert response1.status_code == 201
        
        # Try to create the same user again - should fail
        response2 = await client.post("/auth/register", json=user_data)
        assert response2.status_code == 409  # Conflict


# Integration test combining multiple systems
@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
    async def test_complete_chat_workflow(self, client: AsyncClient, test_model: Model):
        """Test a complete chat workflow from registration to conversation."""
        # 1. Register a user
        user_data = {
            "username": "e2e_user",
            "email": "e2e@example.com",
            "password": "password123",
            "full_name": "E2E Test User"
        }
        
        response = await client.post("/auth/register", json=user_data)
        assert response.status_code == 201
        
        # 2. Login
        login_data = {"username": "e2e_user", "password": "password123"}
        response = await client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create a conversation
        conversation_data = {
            "model_id": test_model.id,
            "title": "E2E Test Conversation",
            "system_prompt": "You are helpful."
        }
        
        response = await client.post("/api/chat/conversations", json=conversation_data, headers=headers)
        assert response.status_code == 200
        
        conversation = response.json()
        conversation_id = conversation["id"]
        
        # 4. Send a message (if chat completion endpoint exists)
        # This might fail if Ollama is not available, but structure should be tested
        chat_data = {
            "model_id": test_model.id,
            "prompt": "Hello, this is a test message.",
            "conversation_id": conversation_id,
            "stream": False
        }
        
        response = await client.post("/api/chat/completions", json=chat_data, headers=headers)
        # Could be 200 (success) or 502/503 (Ollama not available) - both are acceptable for testing
        assert response.status_code in [200, 502, 503]
        
        # 5. List conversations to verify it was created
        response = await client.get("/api/chat/conversations", headers=headers)
        assert response.status_code == 200
        
        conversations = response.json()["conversations"]
        assert len(conversations) >= 1
        assert any(conv["id"] == conversation_id for conv in conversations)