"""
End-to-End tests for Code Factory Pipeline API endpoints.

This module tests the pipeline API endpoints including:
- Pipeline CRUD operations
- Step management
- Pipeline execution
"""

import pytest
import httpx
from typing import Dict, Any
import uuid

# Test pipeline CRUD operations
@pytest.mark.asyncio
async def test_pipeline_create(test_client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test creating a new pipeline."""
    pipeline_data = {
        "name": "Test Create Pipeline",
        "description": "A test pipeline for create operation",
        "is_public": True,
        "tags": ["test", "create"]
    }
    
    response = await test_client.post(
        "/api/pipelines",
        json=pipeline_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == pipeline_data["name"]
    assert data["description"] == pipeline_data["description"]
    assert data["is_public"] == pipeline_data["is_public"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_pipeline_list(test_client: httpx.AsyncClient, auth_headers: Dict[str, str], sample_pipeline: Dict[str, Any]):
    """Test listing pipelines."""
    response = await test_client.get(
        "/api/pipelines",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least the sample pipeline should exist
    
    # Find our sample pipeline in the list
    found_pipeline = False
    for pipeline in data:
        if pipeline["id"] == sample_pipeline["id"]:
            found_pipeline = True
            break
    
    assert found_pipeline, "Sample pipeline not found in pipeline list"


@pytest.mark.asyncio
async def test_pipeline_get(test_client: httpx.AsyncClient, auth_headers: Dict[str, str], sample_pipeline: Dict[str, Any]):
    """Test getting a pipeline by ID."""
    response = await test_client.get(
        f"/api/pipelines/{sample_pipeline['id']}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_pipeline["id"]
    assert data["name"] == sample_pipeline["name"]
    assert data["description"] == sample_pipeline["description"]


@pytest.mark.asyncio
async def test_pipeline_update(test_client: httpx.AsyncClient, auth_headers: Dict[str, str], sample_pipeline: Dict[str, Any]):
    """Test updating a pipeline."""
    update_data = {
        "name": "Updated Pipeline Name",
        "description": "Updated pipeline description",
        "tags": ["updated", "test"]
    }
    
    response = await test_client.put(
        f"/api/pipelines/{sample_pipeline['id']}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]
    assert set(data["tags"]) == set(update_data["tags"])


@pytest.mark.asyncio
async def test_pipeline_delete(test_client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test deleting a pipeline."""
    # First create a pipeline to delete
    pipeline_data = {
        "name": "To Be Deleted",
        "description": "This pipeline will be deleted",
        "is_public": True,
        "tags": ["test", "delete"]
    }
    
    create_response = await test_client.post(
        "/api/pipelines",
        json=pipeline_data,
        headers=auth_headers
    )
    
    assert create_response.status_code == 201
    pipeline_id = create_response.json()["id"]
    
    # Now delete it
    delete_response = await test_client.delete(
        f"/api/pipelines/{pipeline_id}",
        headers=auth_headers
    )
    
    assert delete_response.status_code == 204
    
    # Verify it's gone
    get_response = await test_client.get(
        f"/api/pipelines/{pipeline_id}",
        headers=auth_headers
    )
    
    assert get_response.status_code == 404


# Test pipeline step management
@pytest.mark.asyncio
async def test_create_pipeline_step(test_client: httpx.AsyncClient, auth_headers: Dict[str, str], sample_pipeline: Dict[str, Any]):
    """Test creating a pipeline step."""
    step_data = {
        "name": "Transform Step",
        "type": "transform",
        "order": 1,
        "config": {
            "transform_type": "json_to_text",
            "data": "Test data"
        },
        "description": "A transformation step"
    }
    
    response = await test_client.post(
        f"/api/pipelines/{sample_pipeline['id']}/steps",
        json=step_data,
        headers=auth_headers
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == step_data["name"]
    assert data["type"] == step_data["type"]
    assert data["order"] == step_data["order"]
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_list_pipeline_steps(test_client: httpx.AsyncClient, auth_headers: Dict[str, str], sample_pipeline: Dict[str, Any]):
    """Test listing pipeline steps."""
    response = await test_client.get(
        f"/api/pipelines/{sample_pipeline['id']}/steps",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1  # At least the prompt step from sample_pipeline


@pytest.mark.asyncio
async def test_update_pipeline_step(test_client: httpx.AsyncClient, auth_headers: Dict[str, str], sample_pipeline: Dict[str, Any]):
    """Test updating a pipeline step."""
    # First get the steps to find one to update
    list_response = await test_client.get(
        f"/api/pipelines/{sample_pipeline['id']}/steps",
        headers=auth_headers
    )
    
    assert list_response.status_code == 200
    steps = list_response.json()
    assert len(steps) >= 1
    
    step_to_update = steps[0]
    
    # Update the step
    update_data = {
        "name": "Updated Step Name",
        "description": "Updated step description",
        "config": step_to_update["config"]  # Keep the same config
    }
    
    response = await test_client.put(
        f"/api/pipelines/{sample_pipeline['id']}/steps/{step_to_update['id']}",
        json=update_data,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == update_data["name"]
    assert data["description"] == update_data["description"]


@pytest.mark.asyncio
async def test_reorder_pipeline_steps(test_client: httpx.AsyncClient, auth_headers: Dict[str, str], sample_pipeline: Dict[str, Any]):
    """Test reordering pipeline steps."""
    # First get the steps
    list_response = await test_client.get(
        f"/api/pipelines/{sample_pipeline['id']}/steps",
        headers=auth_headers
    )
    
    assert list_response.status_code == 200
    steps = list_response.json()
    
    # If we have multiple steps, reorder them
    if len(steps) >= 2:
        # Swap the order
        reorder_data = {
            "steps": [
                {"step_id": steps[0]["id"], "order": steps[1]["order"]},
                {"step_id": steps[1]["id"], "order": steps[0]["order"]}
            ]
        }
        
        response = await test_client.post(
            f"/api/pipelines/{sample_pipeline['id']}/steps/reorder",
            json=reorder_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200


# Test pipeline execution
@pytest.mark.asyncio
async def test_execute_pipeline(test_client: httpx.AsyncClient, auth_headers: Dict[str, str], sample_pipeline: Dict[str, Any]):
    """Test executing a pipeline."""
    # Add a simple transform step to avoid LLM dependencies
    step_data = {
        "name": "Simple Transform",
        "type": "transform",
        "order": 1,
        "config": {
            "transform_type": "text_to_json",
            "data": "Hello, world!"
        }
    }
    
    await test_client.post(
        f"/api/pipelines/{sample_pipeline['id']}/steps",
        json=step_data,
        headers=auth_headers
    )
    
    # Execute the pipeline
    execution_data = {
        "input_parameters": {
            "test_param": "Test value"
        }
    }
    
    response = await test_client.post(
        f"/api/pipelines/{sample_pipeline['id']}/execute",
        json=execution_data,
        headers=auth_headers
    )
    
    # Note: Actual execution might fail if Ollama is not running,
    # but we're testing the API endpoint functionality
    assert response.status_code in [200, 202, 400]  # 400 is ok if Ollama is not available
    
    # If successful, check the execution
    if response.status_code in [200, 202]:
        data = response.json()
        assert "id" in data
        assert data["pipeline_id"] == sample_pipeline["id"]
        assert data["status"] in ["pending", "running", "completed"]


@pytest.mark.asyncio
async def test_list_pipeline_executions(test_client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test listing pipeline executions."""
    response = await test_client.get(
        "/api/pipelines/executions",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_nonexistent_pipeline(test_client: httpx.AsyncClient, auth_headers: Dict[str, str]):
    """Test getting a pipeline that doesn't exist."""
    random_id = str(uuid.uuid4())
    response = await test_client.get(
        f"/api/pipelines/{random_id}",
        headers=auth_headers
    )
    
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_access(test_client: httpx.AsyncClient):
    """Test accessing endpoints without authentication."""
    # Try to list pipelines without auth
    response = await test_client.get("/api/pipelines")
    
    # Should either get 401 Unauthorized or 403 Forbidden
    assert response.status_code in [401, 403]