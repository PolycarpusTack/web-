"""
Tests for Pipeline Step Handlers.

These tests focus on the individual step handlers in the pipeline execution engine,
ensuring they process inputs correctly and produce expected outputs.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
import json
import os
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from db.pipeline_models import (
    Pipeline, PipelineStep, PipelineExecution, PipelineStepExecution,
    PipelineExecutionStatus, PipelineStepExecutionStatus, PipelineStepType
)
from pipeline.engine import PipelineEngine, StepExecutionResult, PipelineExecutionError


@pytest.fixture
def mock_db():
    """Creates a mock database session."""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def pipeline_engine(mock_db):
    """Creates an instance of PipelineEngine with a mock database."""
    return PipelineEngine(mock_db)


@pytest.mark.asyncio
async def test_prompt_step_chat_model(pipeline_engine):
    """Tests prompt step with a chat model."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "chat-prompt-step"
    step.type = PipelineStepType.PROMPT.value
    step.config = {
        "model_id": "llama2-chat",
        "prompt": "What is the capital of France?",
        "system_prompt": "You are a helpful assistant."
    }
    
    # Input parameters for the step
    inputs = {
        "model_id": "llama2-chat",
        "prompt": "What is the capital of France?",
        "system_prompt": "You are a helpful assistant.",
        "options": {"temperature": 0.5}
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Mock the model retrieval
    model = MagicMock()
    model.id = "llama2-chat"
    pipeline_engine.db.get_model = AsyncMock(return_value=model)
    
    # Mock the HTTP client response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": "The capital of France is Paris."
        },
        "prompt_eval_count": 15,
        "eval_count": 8
    }
    
    # Mock HTTP client
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    
    # Execute with mocked HTTP client
    with patch('pipeline.engine.main') as mock_main:
        mock_main.app.state.http_client = mock_client
        result = await pipeline_engine._execute_prompt_step(step, inputs, context)
    
    # Check API request
    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/api/chat"
    assert kwargs["json"]["model"] == "llama2-chat"
    assert kwargs["json"]["messages"] == [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
    assert kwargs["json"]["options"] == {"temperature": 0.5}
    
    # Check result
    assert result.success
    assert result.outputs["response"] == "The capital of France is Paris."
    assert result.outputs["model_id"] == "llama2-chat"
    assert result.metrics["tokens_prompt"] == 15
    assert result.metrics["tokens_completion"] == 8
    assert result.metrics["tokens_total"] == 23


@pytest.mark.asyncio
async def test_prompt_step_completion_model(pipeline_engine):
    """Tests prompt step with a completion (non-chat) model."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "completion-prompt-step"
    step.type = PipelineStepType.PROMPT.value
    step.config = {
        "model_id": "llama2",  # Non-chat model
        "prompt": "What is the capital of France?",
        "system_prompt": "You are a helpful assistant."
    }
    
    # Input parameters for the step
    inputs = {
        "model_id": "llama2",
        "prompt": "What is the capital of France?",
        "system_prompt": "You are a helpful assistant."
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Mock the model retrieval
    model = MagicMock()
    model.id = "llama2"
    pipeline_engine.db.get_model = AsyncMock(return_value=model)
    
    # Mock the HTTP client response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "response": "The capital of France is Paris.",
        "prompt_eval_count": 20,
        "eval_count": 10
    }
    
    # Mock HTTP client
    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    
    # Execute with mocked HTTP client
    with patch('pipeline.engine.main') as mock_main:
        mock_main.app.state.http_client = mock_client
        result = await pipeline_engine._execute_prompt_step(step, inputs, context)
    
    # Check API request
    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/api/generate"
    assert kwargs["json"]["model"] == "llama2"
    assert kwargs["json"]["prompt"].startswith("You are a helpful assistant.")
    assert "What is the capital of France?" in kwargs["json"]["prompt"]
    
    # Check result
    assert result.success
    assert result.outputs["response"] == "The capital of France is Paris."
    assert result.outputs["model_id"] == "llama2"
    assert result.metrics["tokens_prompt"] == 20
    assert result.metrics["tokens_completion"] == 10
    assert result.metrics["tokens_total"] == 30


@pytest.mark.asyncio
async def test_prompt_step_error_handling(pipeline_engine):
    """Tests error handling in the prompt step."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "error-prompt-step"
    step.type = PipelineStepType.PROMPT.value
    step.config = {
        "model_id": "invalid-model",
        "prompt": "This will fail"
    }
    
    # Input parameters with missing required field
    inputs = {
        "model_id": "invalid-model",
        # Missing prompt
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Test missing prompt
    result = await pipeline_engine._execute_prompt_step(step, inputs, context)
    assert not result.success
    assert "No prompt provided" in result.error
    
    # Fix input but make the model lookup fail
    inputs["prompt"] = "This will fail"
    pipeline_engine.db.get_model = AsyncMock(return_value=None)
    
    # Test model not found
    result = await pipeline_engine._execute_prompt_step(step, inputs, context)
    assert not result.success
    assert "Model not found" in result.error
    
    # Fix model lookup but make API call fail
    model = MagicMock()
    model.id = "error-model"
    pipeline_engine.db.get_model = AsyncMock(return_value=model)
    
    # Mock HTTP client to raise exception
    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=Exception("API error"))
    
    # Execute with mocked HTTP client
    with patch('pipeline.engine.main') as mock_main:
        mock_main.app.state.http_client = mock_client
        result = await pipeline_engine._execute_prompt_step(step, inputs, context)
    
    # Check error result
    assert not result.success
    assert "Error in prompt step" in result.error
    assert "API error" in result.error


@pytest.mark.asyncio
async def test_code_step_python_execution(pipeline_engine):
    """Tests Python code execution in the code step."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "python-code-step"
    step.type = PipelineStepType.CODE.value
    step.config = {
        "language": "python",
        "code": """
import json
import sys
import os

# Access environment variables passed as parameters
name = os.environ.get('name', 'default')
value = int(os.environ.get('value', '0'))

# Compute result
result = {
    'message': f'Hello, {name}!',
    'value': value,
    'squared': value * value,
    'env_vars': len(os.environ)
}

# Output as JSON
print(json.dumps(result))
"""
    }
    
    # Input parameters
    inputs = {
        "language": "python",
        "code": step.config["code"],
        "parameters": {
            "name": "World",
            "value": "42"
        },
        "timeout": 2
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Mock process execution
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(
        b'{"message": "Hello, World!", "value": 42, "squared": 1764, "env_vars": 30}',
        b''
    ))
    
    # Create a temp file mock
    mock_temp_file = MagicMock()
    mock_temp_file.name = "/tmp/test_code_12345.py"
    
    # Execute with mocked subprocess
    with patch('tempfile.NamedTemporaryFile', return_value=mock_temp_file), \
         patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('os.unlink'):
        
        result = await pipeline_engine._execute_code_step(step, inputs, context)
    
    # Check the command execution
    temp_path = mock_temp_file.name
    assert mock_temp_file.write.called
    
    # Check result
    assert result.success
    assert result.outputs["stdout"] == '{"message": "Hello, World!", "value": 42, "squared": 1764, "env_vars": 30}'
    assert result.outputs["stderr"] == ''
    assert result.outputs["return_code"] == 0
    assert result.outputs["parsed_output"]["message"] == "Hello, World!"
    assert result.outputs["parsed_output"]["value"] == 42
    assert result.outputs["parsed_output"]["squared"] == 1764


@pytest.mark.asyncio
async def test_code_step_timeout(pipeline_engine):
    """Tests timeout handling in code execution."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "timeout-code-step"
    step.type = PipelineStepType.CODE.value
    step.config = {
        "language": "python",
        "code": "import time; time.sleep(10); print('Done')"
    }
    
    # Input parameters with short timeout
    inputs = {
        "language": "python",
        "code": step.config["code"],
        "timeout": 0.1  # Very short timeout
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Create a temp file mock
    mock_temp_file = MagicMock()
    mock_temp_file.name = "/tmp/test_code_timeout.py"
    
    # Mock process that will be killed due to timeout
    mock_process = AsyncMock()
    mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
    mock_process.kill = AsyncMock()
    
    # Execute with mocked subprocess that times out
    with patch('tempfile.NamedTemporaryFile', return_value=mock_temp_file), \
         patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('os.unlink'):
        
        result = await pipeline_engine._execute_code_step(step, inputs, context)
    
    # Check result indicates timeout
    assert not result.success
    assert "timed out" in result.error
    assert mock_process.kill.called


@pytest.mark.asyncio
async def test_code_step_javascript_execution(pipeline_engine):
    """Tests JavaScript code execution in the code step."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "js-code-step"
    step.type = PipelineStepType.CODE.value
    step.config = {
        "language": "javascript",
        "code": """
// Simple JS code
const data = {
    name: "JavaScript Test",
    values: [1, 2, 3, 4, 5],
    sum: function() {
        return this.values.reduce((a, b) => a + b, 0);
    }
};

// Output as JSON
console.log(JSON.stringify({
    name: data.name,
    values: data.values,
    sum: data.sum()
}));
"""
    }
    
    # Input parameters
    inputs = {
        "language": "javascript",
        "code": step.config["code"],
        "timeout": 2
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Mock process execution
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(
        b'{"name":"JavaScript Test","values":[1,2,3,4,5],"sum":15}',
        b''
    ))
    
    # Create a temp file mock
    mock_temp_file = MagicMock()
    mock_temp_file.name = "/tmp/test_code_12345.js"
    
    # Execute with mocked subprocess
    with patch('tempfile.NamedTemporaryFile', return_value=mock_temp_file), \
         patch('asyncio.create_subprocess_exec', return_value=mock_process), \
         patch('os.unlink'):
        
        result = await pipeline_engine._execute_code_step(step, inputs, context)
    
    # Check result
    assert result.success
    assert result.outputs["parsed_output"]["name"] == "JavaScript Test"
    assert result.outputs["parsed_output"]["values"] == [1, 2, 3, 4, 5]
    assert result.outputs["parsed_output"]["sum"] == 15


@pytest.mark.asyncio
async def test_file_step_read_operation(pipeline_engine):
    """Tests file read operation in the file step."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "file-read-step"
    step.type = PipelineStepType.FILE.value
    step.config = {
        "operation": "read",
        "file_path": "/uploads/test-data.json"
    }
    
    # Input parameters
    inputs = {
        "operation": "read",
        "file_path": "/uploads/test-data.json"
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Mock file content
    file_content = '{"name": "Test Data", "values": [1, 2, 3], "active": true}'
    
    # Mock aiofiles and os
    mock_file = AsyncMock()
    mock_file.__aenter__ = AsyncMock(return_value=mock_file)
    mock_file.__aexit__ = AsyncMock(return_value=False)
    mock_file.read = AsyncMock(return_value=file_content)
    
    # Configure mocks
    with patch('pipeline.engine.main') as mock_main, \
         patch('pipeline.engine.aiofiles.open', return_value=mock_file), \
         patch('pipeline.engine.os.path.exists', return_value=True), \
         patch('pipeline.engine.os.path.abspath', return_value="/uploads/test-data.json"), \
         patch('pipeline.engine.os.stat') as mock_stat:
        
        # Mock the uploads directory setting
        mock_main.settings.upload_dir = "/uploads"
        
        # Mock os.stat for file metadata
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = len(file_content)
        mock_stat_result.st_mtime = 1613545200.0
        mock_stat_result.st_ctime = 1613545200.0
        mock_stat.return_value = mock_stat_result
        
        # Execute the file step
        result = await pipeline_engine._execute_file_step(step, inputs, context)
    
    # Check result
    assert result.success
    assert result.outputs["content"]["name"] == "Test Data"
    assert result.outputs["content"]["values"] == [1, 2, 3]
    assert result.outputs["content"]["active"] is True
    assert result.outputs["text"] == file_content
    assert result.outputs["file_info"]["path"] == "/uploads/test-data.json"
    assert result.outputs["file_info"]["size"] == len(file_content)
    assert result.outputs["file_info"]["is_json"] is True


@pytest.mark.asyncio
async def test_file_step_write_operation(pipeline_engine):
    """Tests file write operation in the file step."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "file-write-step"
    step.type = PipelineStepType.FILE.value
    step.config = {
        "operation": "write",
        "file_path": "/uploads/output-data.json"
    }
    
    # Input parameters with complex object to write
    inputs = {
        "operation": "write",
        "file_path": "/uploads/output-data.json",
        "content": {
            "name": "Output Data",
            "timestamp": "2023-06-15T10:30:00Z",
            "records": [
                {"id": 1, "value": "first"},
                {"id": 2, "value": "second"},
                {"id": 3, "value": "third"}
            ],
            "metadata": {
                "author": "test-user",
                "version": "1.0"
            }
        }
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Mock aiofiles and os
    mock_file = AsyncMock()
    mock_file.__aenter__ = AsyncMock(return_value=mock_file)
    mock_file.__aexit__ = AsyncMock(return_value=False)
    mock_file.write = AsyncMock()
    
    # Configure mocks
    with patch('pipeline.engine.main') as mock_main, \
         patch('pipeline.engine.aiofiles.open', return_value=mock_file), \
         patch('pipeline.engine.os.path.exists', return_value=False), \
         patch('pipeline.engine.os.path.abspath', return_value="/uploads/output-data.json"), \
         patch('pipeline.engine.os.path.dirname', return_value="/uploads"), \
         patch('pipeline.engine.os.makedirs') as mock_makedirs, \
         patch('pipeline.engine.os.stat') as mock_stat:
        
        # Mock the uploads directory setting
        mock_main.settings.upload_dir = "/uploads"
        
        # Mock os.stat for file metadata after write
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 200  # Approximate size
        mock_stat.return_value = mock_stat_result
        
        # Execute the file step
        result = await pipeline_engine._execute_file_step(step, inputs, context)
    
    # Check directory was created
    mock_makedirs.assert_called_with("/uploads", exist_ok=True)
    
    # Check file was written with correct content
    mock_file.write.assert_called_once()
    written_content = mock_file.write.call_args[0][0]
    
    # Parse the JSON to check structure
    written_data = json.loads(written_content)
    assert written_data["name"] == "Output Data"
    assert written_data["timestamp"] == "2023-06-15T10:30:00Z"
    assert len(written_data["records"]) == 3
    assert written_data["metadata"]["author"] == "test-user"
    
    # Check result
    assert result.success
    assert result.outputs["written"] is True
    assert "/uploads/output-data.json" in result.outputs["path"]
    assert result.outputs["size"] == 200


@pytest.mark.asyncio
async def test_file_step_security_restrictions(pipeline_engine):
    """Tests security restrictions in the file step to prevent access outside allowed areas."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "file-security-step"
    step.type = PipelineStepType.FILE.value
    step.config = {
        "operation": "read",
        "file_path": "/etc/passwd"  # Attempt to access a system file
    }
    
    # Input parameters
    inputs = {
        "operation": "read",
        "file_path": "/etc/passwd"
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Setup the mocks
    with patch('pipeline.engine.main') as mock_main, \
         patch('pipeline.engine.os.path.abspath') as mock_abspath, \
         patch('pipeline.engine.os.path.basename', return_value="passwd"), \
         patch('pipeline.engine.os.path.exists', return_value=False), \
         patch('pipeline.engine.aiofiles.open') as mock_aiofiles_open:
        
        # Mock the uploads directory setting
        mock_main.settings.upload_dir = "/uploads"
        
        # Mock abspath to return different paths for security check
        mock_abspath.side_effect = lambda path: path if path == "/uploads" else "/etc/passwd"
        
        # Mock open to avoid actual file access
        mock_aiofiles_open.side_effect = FileNotFoundError("File not found")
        
        # Execute the file step
        result = await pipeline_engine._execute_file_step(step, inputs, context)
    
    # Path should be redirected to safe location
    assert not result.success
    assert "File not found" in result.error


@pytest.mark.asyncio
async def test_api_step_get_request(pipeline_engine):
    """Tests API step with GET request."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "api-get-step"
    step.type = PipelineStepType.API.value
    step.config = {
        "method": "GET",
        "url": "https://api.example.com/users"
    }
    
    # Input parameters
    inputs = {
        "method": "GET",
        "url": "https://api.example.com/users",
        "params": {"page": 1, "limit": 10},
        "headers": {"Authorization": "Bearer token123"}
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.elapsed.total_seconds.return_value = 0.235
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.text = '{"users": [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}], "total": 2}'
    mock_response.content = mock_response.text.encode()
    mock_response.json.return_value = {
        "users": [
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Jane"}
        ],
        "total": 2
    }
    
    # Mock HTTP client
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)
    
    # Execute the API step
    with patch('pipeline.engine.httpx.AsyncClient', return_value=mock_client):
        result = await pipeline_engine._execute_api_step(step, inputs, context)
    
    # Check the request was made with correct parameters
    mock_client.get.assert_called_once_with(
        "https://api.example.com/users",
        headers={"Authorization": "Bearer token123"},
        params={"page": 1, "limit": 10}
    )
    
    # Check result
    assert result.success
    assert result.outputs["status"] == 200
    assert result.outputs["is_json"] is True
    assert len(result.outputs["body"]["users"]) == 2
    assert result.outputs["body"]["users"][0]["name"] == "John"
    
    # Check metrics
    assert result.metrics["status_code"] == 200
    assert result.metrics["response_time_ms"] == 235.0
    assert result.metrics["content_length"] == len(mock_response.content)


@pytest.mark.asyncio
async def test_api_step_post_request(pipeline_engine):
    """Tests API step with POST request."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "api-post-step"
    step.type = PipelineStepType.API.value
    step.config = {
        "method": "POST",
        "url": "https://api.example.com/users"
    }
    
    # Input parameters
    inputs = {
        "method": "POST",
        "url": "https://api.example.com/users",
        "headers": {"Content-Type": "application/json"},
        "data": {
            "name": "Alice",
            "email": "alice@example.com",
            "role": "admin"
        }
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Mock response
    mock_response = MagicMock()
    mock_response.status_code = 201
    mock_response.elapsed.total_seconds.return_value = 0.328
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.text = '{"id": 3, "name": "Alice", "email": "alice@example.com", "role": "admin"}'
    mock_response.content = mock_response.text.encode()
    mock_response.json.return_value = {
        "id": 3,
        "name": "Alice",
        "email": "alice@example.com",
        "role": "admin"
    }
    
    # Mock HTTP client
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=mock_response)
    
    # Execute the API step
    with patch('pipeline.engine.httpx.AsyncClient', return_value=mock_client):
        result = await pipeline_engine._execute_api_step(step, inputs, context)
    
    # Check the request was made with correct parameters
    mock_client.post.assert_called_once_with(
        "https://api.example.com/users",
        headers={"Content-Type": "application/json"},
        json=inputs["data"],
        params=None
    )
    
    # Check result
    assert result.success
    assert result.outputs["status"] == 201
    assert result.outputs["is_json"] is True
    assert result.outputs["body"]["id"] == 3
    assert result.outputs["body"]["name"] == "Alice"
    
    # Check metrics
    assert result.metrics["status_code"] == 201
    assert result.metrics["response_time_ms"] == 328.0


@pytest.mark.asyncio
async def test_api_step_error_response(pipeline_engine):
    """Tests API step with an error response."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "api-error-step"
    step.type = PipelineStepType.API.value
    step.config = {
        "method": "DELETE",
        "url": "https://api.example.com/users/999"
    }
    
    # Input parameters
    inputs = {
        "method": "DELETE",
        "url": "https://api.example.com/users/999",
        "headers": {"Authorization": "Bearer token123"}
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Mock error response
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.reason_phrase = "Not Found"
    mock_response.elapsed.total_seconds.return_value = 0.156
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.text = '{"error": "User not found", "code": "USER_NOT_FOUND"}'
    mock_response.content = mock_response.text.encode()
    mock_response.json.return_value = {
        "error": "User not found",
        "code": "USER_NOT_FOUND"
    }
    
    # Mock HTTP client
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.delete = AsyncMock(return_value=mock_response)
    
    # Execute the API step
    with patch('pipeline.engine.httpx.AsyncClient', return_value=mock_client):
        result = await pipeline_engine._execute_api_step(step, inputs, context)
    
    # Check result indicates failure
    assert not result.success
    assert "API request failed with status 404" in result.error
    assert result.outputs["status"] == 404
    assert result.outputs["is_json"] is True
    assert result.outputs["body"]["error"] == "User not found"
    
    # Check metrics
    assert result.metrics["status_code"] == 404
    assert result.metrics["response_time_ms"] == 156.0


@pytest.mark.asyncio
async def test_api_step_network_error(pipeline_engine):
    """Tests API step with a network error."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "api-network-error-step"
    step.type = PipelineStepType.API.value
    step.config = {
        "method": "GET",
        "url": "https://api.example.com/timeout"
    }
    
    # Input parameters
    inputs = {
        "method": "GET",
        "url": "https://api.example.com/timeout",
        "timeout": 5
    }
    
    # Context for execution
    context = {"user_id": "test-user", "pipeline_id": "test-pipeline"}
    
    # Mock HTTP client that raises a connection error
    import httpx
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    
    # Execute the API step
    with patch('pipeline.engine.httpx.AsyncClient', return_value=mock_client):
        result = await pipeline_engine._execute_api_step(step, inputs, context)
    
    # Check result indicates failure
    assert not result.success
    assert "HTTP request error" in result.error
    assert "Connection refused" in result.error


def test_get_value_from_context_simple(pipeline_engine):
    """Tests simple value retrieval from context."""
    context = {
        "input": {
            "query": "Simple input value"
        },
        "output": {
            "result1": "Simple output value",
            "result2": 42
        }
    }
    
    # Get from output (default source)
    assert pipeline_engine._get_value_from_context("result1", context) == "Simple output value"
    assert pipeline_engine._get_value_from_context("result2", context) == 42
    
    # Get from input with explicit source
    assert pipeline_engine._get_value_from_context({"source": "input", "path": "query"}, context) == "Simple input value"
    
    # Missing values
    assert pipeline_engine._get_value_from_context("missing", context) is None
    assert pipeline_engine._get_value_from_context({"source": "missing", "path": "key"}, context) is None


def test_get_value_from_context_nested(pipeline_engine):
    """Tests nested value retrieval from context."""
    context = {
        "input": {
            "user": {
                "name": "Test User",
                "preferences": {
                    "theme": "dark",
                    "notifications": True
                }
            }
        },
        "output": {
            "analysis": {
                "scores": [85, 90, 78],
                "average": 84.33,
                "details": {
                    "strengths": ["speed", "accuracy"],
                    "weaknesses": ["consistency"]
                }
            },
            "processed": True
        }
    }
    
    # Nested dot paths in output
    assert pipeline_engine._get_value_from_context("analysis.average", context) == 84.33
    assert pipeline_engine._get_value_from_context("analysis.scores", context) == [85, 90, 78]
    assert pipeline_engine._get_value_from_context("analysis.details.strengths", context) == ["speed", "accuracy"]
    
    # Nested dot paths in input
    assert pipeline_engine._get_value_from_context(
        {"source": "input", "path": "user.name"}, context) == "Test User"
    assert pipeline_engine._get_value_from_context(
        {"source": "input", "path": "user.preferences.theme"}, context) == "dark"
    
    # Partial path exists but final part doesn't
    assert pipeline_engine._get_value_from_context("analysis.missing", context) is None
    assert pipeline_engine._get_value_from_context("analysis.details.missing", context) is None
    
    # Path doesn't exist at all
    assert pipeline_engine._get_value_from_context("completely.missing.path", context) is None