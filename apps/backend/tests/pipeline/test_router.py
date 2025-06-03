"""
Tests for the Pipeline Router.

This module tests the FastAPI routes for pipeline management, focusing on:
1. Creating pipelines
2. Retrieving pipelines
3. Managing pipeline steps
4. Executing pipelines
"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from fastapi.testclient import TestClient

from sqlalchemy.ext.asyncio import AsyncSession

from db.pipeline_models import (
    Pipeline, PipelineStep, PipelineExecution, PipelineStepExecution,
    PipelineExecutionStatus, PipelineStepExecutionStatus, PipelineStepType
)
from pipeline.router import router, create_new_pipeline, list_pipelines, get_pipeline_by_id
from pipeline.schemas import PipelineCreate, PipelineUpdate
from auth.schemas import User


@pytest.fixture
def mock_db():
    """Creates a mock database session."""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def mock_current_user():
    """Creates a mock authenticated user."""
    user = MagicMock(spec=User)
    user.id = "test-user-id"
    user.username = "testuser"
    user.is_active = True
    return user


@pytest.fixture
def mock_pipeline():
    """Creates a mock pipeline."""
    pipeline = MagicMock(spec=Pipeline)
    pipeline.id = "test-pipeline-id"
    pipeline.name = "Test Pipeline"
    pipeline.description = "A test pipeline"
    pipeline.user_id = "test-user-id"
    pipeline.is_active = True
    pipeline.is_public = False
    pipeline.created_at = "2023-01-01T00:00:00"
    pipeline.updated_at = "2023-01-01T01:00:00"
    pipeline.version = "1.0"
    pipeline.tags = ["test", "api"]
    return pipeline


@pytest.fixture
def mock_pipelines(mock_pipeline):
    """Creates a list of mock pipelines."""
    pipelines = [mock_pipeline]
    
    # Add a second pipeline
    pipeline2 = MagicMock(spec=Pipeline)
    pipeline2.id = "test-pipeline-id-2"
    pipeline2.name = "Test Pipeline 2"
    pipeline2.description = "Another test pipeline"
    pipeline2.user_id = "test-user-id"
    pipeline2.is_active = True
    pipeline2.is_public = True
    pipeline2.created_at = "2023-01-02T00:00:00"
    pipeline2.updated_at = "2023-01-02T01:00:00"
    pipeline2.version = "1.0"
    pipeline2.tags = ["test", "public"]
    
    pipelines.append(pipeline2)
    return pipelines


@pytest.mark.asyncio
async def test_create_new_pipeline(mock_db, mock_current_user, mock_pipeline):
    """Tests creating a new pipeline."""
    # Mock the create_pipeline function
    with patch("pipeline.router.create_pipeline", return_value=mock_pipeline) as mock_create:
        # Create pipeline data
        pipeline_data = PipelineCreate(
            name="Test Pipeline",
            description="A test pipeline",
            is_public=False,
            tags=["test", "api"]
        )
        
        # Call the endpoint function
        result = await create_new_pipeline(pipeline_data, mock_db, mock_current_user)
        
        # Verify the create function was called with correct parameters
        mock_create.assert_called_once_with(
            db=mock_db,
            user_id=mock_current_user.id,
            name=pipeline_data.name,
            description=pipeline_data.description,
            is_public=pipeline_data.is_public,
            tags=pipeline_data.tags,
            config=pipeline_data.config
        )
        
        # Verify the result
        assert result == mock_pipeline


@pytest.mark.asyncio
async def test_list_pipelines(mock_db, mock_current_user, mock_pipelines):
    """Tests listing pipelines."""
    # Mock the get_pipelines function
    with patch("pipeline.router.get_pipelines", return_value=mock_pipelines) as mock_get:
        # Call the endpoint function
        result = await list_pipelines(None, True, 0, 20, mock_db, mock_current_user)
        
        # Verify the get function was called with correct parameters
        mock_get.assert_called_once_with(
            db=mock_db,
            user_id=mock_current_user.id,
            include_public=True,
            tags=None,
            skip=0,
            limit=20
        )
        
        # Verify the result
        assert result == mock_pipelines
        assert len(result) == 2


@pytest.mark.asyncio
async def test_list_pipelines_with_tags(mock_db, mock_current_user, mock_pipelines):
    """Tests listing pipelines with tag filtering."""
    # Mock the get_pipelines function
    with patch("pipeline.router.get_pipelines", return_value=[mock_pipelines[0]]) as mock_get:
        # Call the endpoint function with tags
        result = await list_pipelines(["api"], True, 0, 20, mock_db, mock_current_user)
        
        # Verify the get function was called with correct parameters
        mock_get.assert_called_once_with(
            db=mock_db,
            user_id=mock_current_user.id,
            include_public=True,
            tags=["api"],
            skip=0,
            limit=20
        )
        
        # Verify the result
        assert result == [mock_pipelines[0]]
        assert len(result) == 1


@pytest.mark.asyncio
async def test_get_pipeline_by_id(mock_db, mock_current_user, mock_pipeline):
    """Tests getting a pipeline by ID."""
    # Mock the get_pipeline function
    with patch("pipeline.router.get_pipeline", return_value=mock_pipeline) as mock_get:
        # Call the endpoint function
        result = await get_pipeline_by_id(mock_pipeline.id, mock_db, mock_current_user)
        
        # Verify the get function was called with correct parameters
        mock_get.assert_called_once_with(mock_db, mock_pipeline.id)
        
        # Verify the result
        assert result == mock_pipeline


@pytest.mark.asyncio
async def test_get_pipeline_by_id_not_found(mock_db, mock_current_user):
    """Tests getting a non-existent pipeline."""
    # Mock the get_pipeline function to return None
    with patch("pipeline.router.get_pipeline", return_value=None) as mock_get:
        # Call should raise HTTPException with 404
        with pytest.raises(HTTPException) as excinfo:
            await get_pipeline_by_id("nonexistent-id", mock_db, mock_current_user)
        
        # Verify the exception
        assert excinfo.value.status_code == 404
        assert "Pipeline not found" in excinfo.value.detail


@pytest.mark.asyncio
async def test_get_pipeline_by_id_unauthorized(mock_db, mock_current_user, mock_pipeline):
    """Tests getting a pipeline without permission."""
    # Make the pipeline private and owned by another user
    mock_pipeline.is_public = False
    mock_pipeline.user_id = "another-user-id"
    
    # Mock the get_pipeline function
    with patch("pipeline.router.get_pipeline", return_value=mock_pipeline) as mock_get:
        # Call should raise HTTPException with 403
        with pytest.raises(HTTPException) as excinfo:
            await get_pipeline_by_id(mock_pipeline.id, mock_db, mock_current_user)
        
        # Verify the exception
        assert excinfo.value.status_code == 403
        assert "Not authorized" in excinfo.value.detail


@pytest.mark.asyncio
async def test_update_pipeline_by_id(mock_db, mock_current_user, mock_pipeline):
    """Tests updating a pipeline."""
    # Mock the get_pipeline and update_pipeline functions
    with patch("pipeline.router.get_pipeline", return_value=mock_pipeline) as mock_get:
        with patch("pipeline.router.update_pipeline", return_value=mock_pipeline) as mock_update:
            # Create update data
            pipeline_data = PipelineUpdate(
                name="Updated Pipeline",
                description="Updated description",
                is_public=True
            )
            
            # Call the endpoint function
            result = await update_pipeline_by_id(pipeline_data, mock_pipeline.id, mock_db, mock_current_user)
            
            # Verify the get and update functions were called with correct parameters
            mock_get.assert_called_once_with(mock_db, mock_pipeline.id)
            mock_update.assert_called_once()
            
            # Verify the result
            assert result == mock_pipeline


@pytest.mark.asyncio
async def test_execute_pipeline_success(mock_db, mock_current_user, mock_pipeline):
    """Tests executing a pipeline successfully."""
    # Mock execution result
    mock_execution = MagicMock(spec=PipelineExecution)
    mock_execution.id = "test-execution-id"
    mock_execution.status = PipelineExecutionStatus.COMPLETED.value
    
    # Mock the engine and execution
    with patch("pipeline.router.get_pipeline", return_value=mock_pipeline) as mock_get:
        with patch("pipeline.router.PipelineEngine") as MockEngine:
            # Configure mock engine
            mock_engine_instance = MockEngine.return_value
            mock_engine_instance.execute_pipeline.return_value = mock_execution
            
            # Call the endpoint function
            from pipeline.schemas import PipelineExecuteRequest
            result = await execute_pipeline_endpoint(
                PipelineExecuteRequest(input_parameters={"query": "test"}),
                mock_pipeline.id, 
                mock_db, 
                mock_current_user
            )
            
            # Verify the get function and engine were called correctly
            mock_get.assert_called_once_with(mock_db, mock_pipeline.id)
            MockEngine.assert_called_once_with(mock_db)
            mock_engine_instance.execute_pipeline.assert_called_once_with(
                pipeline_id=mock_pipeline.id,
                user_id=mock_current_user.id,
                input_parameters={"query": "test"}
            )
            
            # Verify the result
            assert result == mock_execution


# Import the execution endpoint function for testing
from pipeline.router import execute_pipeline_endpoint