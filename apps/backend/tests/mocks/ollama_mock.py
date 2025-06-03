"""
Mock service for Ollama API to avoid external dependencies in tests.
"""
from unittest.mock import AsyncMock, MagicMock
import httpx
from datetime import datetime
from typing import Dict, List, Any


class MockOllamaResponse:
    """Mock response for Ollama API calls."""
    
    def __init__(self, status_code: int = 200, json_data: Dict[str, Any] = None):
        self.status_code = status_code
        self._json_data = json_data or {}
    
    def json(self):
        return self._json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPError(f"HTTP {self.status_code}")


class MockOllamaClient:
    """Mock Ollama client for testing."""
    
    def __init__(self):
        self.models = [
            {
                "name": "llama2:7b",
                "modified_at": "2023-12-01T10:00:00Z",
                "size": 3826793730,
                "digest": "sha256:abc123",
                "details": {
                    "format": "gguf",
                    "family": "llama",
                    "families": ["llama"],
                    "parameter_size": "7B",
                    "quantization_level": "Q4_0"
                }
            },
            {
                "name": "mistral:latest",
                "modified_at": "2023-12-01T12:00:00Z",
                "size": 4109000000,
                "digest": "sha256:def456",
                "details": {
                    "format": "gguf",
                    "family": "mistral",
                    "families": ["mistral"],
                    "parameter_size": "7B",
                    "quantization_level": "Q4_0"
                }
            }
        ]
        
        self.running_models = []
    
    async def get_models(self) -> MockOllamaResponse:
        """Mock get models endpoint."""
        return MockOllamaResponse(200, {"models": self.models})
    
    async def get_model_info(self, model_name: str) -> MockOllamaResponse:
        """Mock get model info endpoint."""
        model = next((m for m in self.models if m["name"] == model_name), None)
        if not model:
            return MockOllamaResponse(404, {"error": "model not found"})
        return MockOllamaResponse(200, model)
    
    async def get_running_models(self) -> MockOllamaResponse:
        """Mock get running models endpoint."""
        return MockOllamaResponse(200, {"models": self.running_models})
    
    async def pull_model(self, model_name: str) -> MockOllamaResponse:
        """Mock pull model endpoint."""
        # Simulate successful pull
        new_model = {
            "name": model_name,
            "modified_at": datetime.now().isoformat() + "Z",
            "size": 4000000000,
            "digest": "sha256:new123",
            "details": {
                "format": "gguf",
                "family": "unknown",
                "families": ["unknown"],
                "parameter_size": "Unknown",
                "quantization_level": "Q4_0"
            }
        }
        
        # Add to models if not exists
        if not any(m["name"] == model_name for m in self.models):
            self.models.append(new_model)
        
        return MockOllamaResponse(200, {"status": "success"})
    
    async def delete_model(self, model_name: str) -> MockOllamaResponse:
        """Mock delete model endpoint."""
        self.models = [m for m in self.models if m["name"] != model_name]
        return MockOllamaResponse(200, {"status": "success"})
    
    async def start_model(self, model_name: str) -> MockOllamaResponse:
        """Mock start model endpoint."""
        model = next((m for m in self.models if m["name"] == model_name), None)
        if not model:
            return MockOllamaResponse(404, {"error": "model not found"})
        
        if model not in self.running_models:
            self.running_models.append(model)
        
        return MockOllamaResponse(200, {"status": "success"})
    
    async def stop_model(self, model_name: str) -> MockOllamaResponse:
        """Mock stop model endpoint."""
        self.running_models = [m for m in self.running_models if m["name"] != model_name]
        return MockOllamaResponse(200, {"status": "success"})
    
    async def generate(self, model_name: str, prompt: str, **kwargs) -> MockOllamaResponse:
        """Mock generate endpoint."""
        model = next((m for m in self.models if m["name"] == model_name), None)
        if not model:
            return MockOllamaResponse(404, {"error": "model not found"})
        
        # Mock response
        response = {
            "model": model_name,
            "created_at": datetime.now().isoformat() + "Z",
            "response": f"Mock response to: {prompt[:50]}...",
            "done": True,
            "context": [1, 2, 3, 4, 5],  # Mock context tokens
            "total_duration": 1000000000,  # 1 second in nanoseconds
            "load_duration": 100000000,
            "prompt_eval_count": 10,
            "prompt_eval_duration": 500000000,
            "eval_count": 20,
            "eval_duration": 400000000
        }
        
        return MockOllamaResponse(200, response)
    
    async def chat(self, model_name: str, messages: List[Dict], **kwargs) -> MockOllamaResponse:
        """Mock chat endpoint."""
        model = next((m for m in self.models if m["name"] == model_name), None)
        if not model:
            return MockOllamaResponse(404, {"error": "model not found"})
        
        last_message = messages[-1]["content"] if messages else "Hello"
        
        # Mock chat response
        response = {
            "model": model_name,
            "created_at": datetime.now().isoformat() + "Z",
            "message": {
                "role": "assistant",
                "content": f"Mock chat response to: {last_message[:50]}..."
            },
            "done": True,
            "total_duration": 1000000000,
            "load_duration": 100000000,
            "prompt_eval_count": len(str(messages)),
            "prompt_eval_duration": 500000000,
            "eval_count": 25,
            "eval_duration": 400000000
        }
        
        return MockOllamaResponse(200, response)


# Global mock instance
mock_ollama_client = MockOllamaClient()


def mock_ollama_request(method: str, url: str, **kwargs) -> MockOllamaResponse:
    """Mock function to replace httpx requests to Ollama."""
    
    # Parse the URL to determine the endpoint
    if "/api/tags" in url:
        return mock_ollama_client.get_models()
    elif "/api/show" in url:
        # Extract model name from request
        json_data = kwargs.get("json", {})
        model_name = json_data.get("name", "unknown")
        return mock_ollama_client.get_model_info(model_name)
    elif "/api/ps" in url:
        return mock_ollama_client.get_running_models()
    elif "/api/pull" in url:
        json_data = kwargs.get("json", {})
        model_name = json_data.get("name", "unknown")
        return mock_ollama_client.pull_model(model_name)
    elif "/api/delete" in url:
        json_data = kwargs.get("json", {})
        model_name = json_data.get("name", "unknown")
        return mock_ollama_client.delete_model(model_name)
    elif "/api/generate" in url:
        json_data = kwargs.get("json", {})
        model_name = json_data.get("model", "unknown")
        prompt = json_data.get("prompt", "")
        return mock_ollama_client.generate(model_name, prompt, **kwargs)
    elif "/api/chat" in url:
        json_data = kwargs.get("json", {})
        model_name = json_data.get("model", "unknown")
        messages = json_data.get("messages", [])
        return mock_ollama_client.chat(model_name, messages, **kwargs)
    else:
        return MockOllamaResponse(404, {"error": "endpoint not found"})


# Pytest fixtures for mocking
import pytest
from unittest.mock import patch, AsyncMock


@pytest.fixture
def mock_ollama():
    """Fixture to mock all Ollama API calls."""
    with patch('httpx.AsyncClient.request', side_effect=mock_ollama_request) as mock:
        yield mock


@pytest.fixture
def mock_ollama_post():
    """Fixture to mock Ollama POST requests specifically."""
    with patch('httpx.AsyncClient.post', side_effect=lambda url, **kwargs: mock_ollama_request("POST", url, **kwargs)) as mock:
        yield mock


@pytest.fixture
def mock_ollama_get():
    """Fixture to mock Ollama GET requests specifically."""
    with patch('httpx.AsyncClient.get', side_effect=lambda url, **kwargs: mock_ollama_request("GET", url, **kwargs)) as mock:
        yield mock