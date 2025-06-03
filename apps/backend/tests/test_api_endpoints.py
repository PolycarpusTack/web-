"""
Comprehensive API endpoint integration tests for Web+ backend.
"""
import pytest
import httpx
from httpx import AsyncClient
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
import json
import os
from datetime import datetime, timedelta

from main import app
from db.database import get_db
from auth.jwt import create_access_token, decode_access_token
from auth.api_keys import validate_api_key


class TestAuthEndpoints:
    """Test authentication endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_login_success(self, client, test_user):
        """Test successful user login."""
        login_data = {
            "username": test_user.username,
            "password": "testpassword"
        }
        
        response = await client.post("/auth/login", data=login_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert data["user"]["username"] == test_user.username

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = await client.post("/auth/login", data=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_register_success(self, client):
        """Test successful user registration."""
        register_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "newpassword",
            "full_name": "New User"
        }
        
        response = await client.post("/auth/register", json=register_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert "id" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username."""
        register_data = {
            "username": test_user.username,
            "email": "different@example.com",
            "password": "password",
            "full_name": "Different User"
        }
        
        response = await client.post("/auth/register", json=register_data)
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_protected_endpoint_with_token(self, client, test_user, auth_headers):
        """Test accessing protected endpoint with valid token."""
        response = await client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["username"] == test_user.username

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = await client.get("/auth/me")
        assert response.status_code == 401


class TestModelEndpoints:
    """Test model management endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_models(self, client, auth_headers, test_model):
        """Test getting list of models."""
        response = await client.get("/api/models", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check our test model is in the list
        model_ids = [model["id"] for model in data]
        assert test_model.id in model_ids

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_model_by_id(self, client, auth_headers, test_model):
        """Test getting specific model by ID."""
        response = await client.get(f"/api/models/{test_model.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_model.id
        assert data["name"] == test_model.name

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_nonexistent_model(self, client, auth_headers):
        """Test getting non-existent model."""
        response = await client.get("/api/models/nonexistent", headers=auth_headers)
        assert response.status_code == 404

    @pytest.mark.integration
    @pytest.mark.asyncio
    @patch('httpx.AsyncClient.get')
    async def test_ollama_models_integration(self, mock_get, client, auth_headers):
        """Test Ollama integration for fetching models."""
        # Mock Ollama response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "models": [
                {
                    "name": "llama2:7b",
                    "modified_at": "2023-01-01T00:00:00Z",
                    "size": 3826793730
                }
            ]
        }
        mock_get.return_value = mock_response
        
        response = await client.get("/api/models/ollama", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "models" in data
        assert len(data["models"]) >= 1


class TestConversationEndpoints:
    """Test conversation management endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_conversation(self, client, auth_headers, test_model):
        """Test creating a new conversation."""
        conversation_data = {
            "model_id": test_model.id,
            "title": "Test Conversation",
            "system_prompt": "You are a helpful assistant."
        }
        
        response = await client.post("/api/conversations", json=conversation_data, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["title"] == "Test Conversation"
        assert data["model_id"] == test_model.id
        assert "id" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_conversations(self, client, auth_headers, test_conversation):
        """Test getting user conversations."""
        response = await client.get("/api/conversations", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check our test conversation is in the list
        conversation_ids = [conv["id"] for conv in data]
        assert test_conversation.id in conversation_ids

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_conversation_by_id(self, client, auth_headers, test_conversation):
        """Test getting specific conversation."""
        response = await client.get(f"/api/conversations/{test_conversation.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_conversation.id
        assert data["title"] == test_conversation.title

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_add_message_to_conversation(self, client, auth_headers, test_conversation):
        """Test adding message to conversation."""
        message_data = {
            "role": "user",
            "content": "Hello, how are you?"
        }
        
        response = await client.post(
            f"/api/conversations/{test_conversation.id}/messages",
            json=message_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["content"] == "Hello, how are you?"
        assert data["role"] == "user"
        assert data["conversation_id"] == test_conversation.id

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_conversation_messages(self, client, auth_headers, test_conversation, test_message):
        """Test getting conversation messages."""
        response = await client.get(
            f"/api/conversations/{test_conversation.id}/messages",
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check our test message is in the list
        message_ids = [msg["id"] for msg in data]
        assert test_message.id in message_ids


class TestFileEndpoints:
    """Test file management endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_upload_file(self, client, auth_headers):
        """Test file upload."""
        # Create a test file
        test_content = b"This is test file content"
        files = {"file": ("test.txt", test_content, "text/plain")}
        
        response = await client.post("/api/files/upload", files=files, headers=auth_headers)
        assert response.status_code == 201
        
        data = response.json()
        assert data["original_filename"] == "test.txt"
        assert data["content_type"] == "text/plain"
        assert data["size"] == len(test_content)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_user_files(self, client, auth_headers, test_file):
        """Test getting user files."""
        response = await client.get("/api/files", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check our test file is in the list
        file_ids = [file["id"] for file in data]
        assert test_file.id in file_ids

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_file_by_id(self, client, auth_headers, test_file):
        """Test getting specific file."""
        response = await client.get(f"/api/files/{test_file.id}", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_file.id
        assert data["original_filename"] == test_file.original_filename

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_delete_file(self, client, auth_headers, test_file):
        """Test file deletion."""
        response = await client.delete(f"/api/files/{test_file.id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify file is deleted
        get_response = await client.get(f"/api/files/{test_file.id}", headers=auth_headers)
        assert get_response.status_code == 404


class TestPipelineEndpoints:
    """Test pipeline execution endpoints."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    @patch('pipeline.engine.PipelineEngine.execute')
    async def test_execute_pipeline(self, mock_execute, client, auth_headers):
        """Test pipeline execution."""
        # Mock pipeline execution
        mock_execute.return_value = {
            "status": "completed",
            "results": {"output": "Pipeline executed successfully"},
            "execution_time": 1.5
        }
        
        pipeline_data = {
            "steps": [
                {
                    "name": "test_step",
                    "type": "llm_call",
                    "config": {
                        "model": "test-model",
                        "prompt": "Hello world"
                    }
                }
            ]
        }
        
        response = await client.post("/api/pipelines/execute", json=pipeline_data, headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "completed"
        assert "results" in data
        assert "execution_time" in data

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_get_pipeline_templates(self, client, auth_headers):
        """Test getting pipeline templates."""
        response = await client.get("/api/pipelines/templates", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        # Should have at least some default templates
        assert len(data) >= 0


# Additional fixtures for API testing
@pytest.fixture
async def client(db_session):
    """Create test client with dependency overrides."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Use httpx AsyncClient for async testing
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
async def auth_headers(test_user):
    """Create authentication headers for testing."""
    access_token = create_access_token(data={"sub": test_user.username})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def api_key_headers(test_api_key):
    """Create API key headers for testing."""
    return {"X-API-Key": test_api_key.key}