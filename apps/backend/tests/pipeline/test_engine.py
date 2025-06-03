"""
Tests for the Pipeline Engine.

This module tests the pipeline execution engine, focusing on:
1. Step execution
2. Context management
3. Input/output mapping
4. Error handling
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.fixture
def mock_pipeline():
    """Creates a mock pipeline."""
    pipeline = MagicMock(spec=Pipeline)
    pipeline.id = "test-pipeline-id"
    pipeline.name = "Test Pipeline"
    pipeline.user_id = "test-user-id"
    pipeline.is_public = False
    return pipeline


@pytest.fixture
def mock_steps():
    """Creates a list of mock pipeline steps."""
    steps = []
    
    # Step 1: Prompt step
    prompt_step = MagicMock(spec=PipelineStep)
    prompt_step.id = "step1"
    prompt_step.name = "Generate Prompt"
    prompt_step.type = PipelineStepType.PROMPT.value
    prompt_step.order = 1
    prompt_step.config = {
        "model_id": "test-model",
        "prompt": "Generate a response to: {{input.query}}"
    }
    prompt_step.input_mapping = {
        "prompt": "input.query"
    }
    prompt_step.output_mapping = {
        "generated_text": "response"
    }
    
    # Step 2: Transform step
    transform_step = MagicMock(spec=PipelineStep)
    transform_step.id = "step2"
    transform_step.name = "Process Response"
    transform_step.type = PipelineStepType.TRANSFORM.value
    transform_step.order = 2
    transform_step.config = {
        "transform_type": "text_to_json"
    }
    transform_step.input_mapping = {
        "data": "output.generated_text"
    }
    
    steps.append(prompt_step)
    steps.append(transform_step)
    return steps


@pytest.mark.asyncio
async def test_execute_pipeline_success(pipeline_engine, mock_pipeline, mock_steps):
    """Tests successful pipeline execution."""
    # Mock database calls
    pipeline_engine.db.get_pipeline = AsyncMock(return_value=mock_pipeline)
    pipeline_engine.db.get_pipeline_steps = AsyncMock(return_value=mock_steps)
    
    # Create mock execution
    mock_execution = MagicMock(spec=PipelineExecution)
    mock_execution.id = "test-execution-id"
    pipeline_engine.db.create_pipeline_execution = AsyncMock(return_value=mock_execution)
    
    # Mock step execution creation
    mock_step_exec = MagicMock(spec=PipelineStepExecution)
    mock_step_exec.id = "test-step-execution-id"
    pipeline_engine.db.create_pipeline_step_execution = AsyncMock(return_value=mock_step_exec)
    
    # Mock step execution updating
    pipeline_engine.db.update_pipeline_step_execution = AsyncMock()
    pipeline_engine.db.complete_pipeline_step_execution = AsyncMock()
    pipeline_engine.db.complete_pipeline_execution = AsyncMock(return_value=mock_execution)
    
    # Mock the step handlers
    prompt_result = StepExecutionResult.success_result(
        outputs={"response": "Generated response text"}, 
        metrics={"tokens": 100}
    )
    transform_result = StepExecutionResult.success_result(
        outputs={"result": {"parsed": "Generated response text"}}
    )
    
    with patch.object(pipeline_engine, '_execute_prompt_step', return_value=prompt_result):
        with patch.object(pipeline_engine, '_execute_transform_step', return_value=transform_result):
            # Execute the pipeline
            result = await pipeline_engine.execute_pipeline(
                pipeline_id=mock_pipeline.id,
                user_id=mock_pipeline.user_id,
                input_parameters={"query": "Test query"}
            )
    
    # Verify the execution was created and updated
    pipeline_engine.db.create_pipeline_execution.assert_called_once()
    pipeline_engine.db.complete_pipeline_execution.assert_called_with(
        pipeline_engine.db,
        mock_execution.id,
        PipelineExecutionStatus.COMPLETED,
        results={"generated_text": "Generated response text", "result": {"parsed": "Generated response text"}}
    )
    
    # Each step should have been executed
    assert pipeline_engine.db.create_pipeline_step_execution.call_count == 2
    assert pipeline_engine.db.complete_pipeline_step_execution.call_count == 2


@pytest.mark.asyncio
async def test_execute_pipeline_error(pipeline_engine, mock_pipeline, mock_steps):
    """Tests pipeline execution with an error."""
    # Mock database calls
    pipeline_engine.db.get_pipeline = AsyncMock(return_value=mock_pipeline)
    pipeline_engine.db.get_pipeline_steps = AsyncMock(return_value=mock_steps)
    
    # Create mock execution
    mock_execution = MagicMock(spec=PipelineExecution)
    mock_execution.id = "test-execution-id"
    pipeline_engine.db.create_pipeline_execution = AsyncMock(return_value=mock_execution)
    
    # Mock step execution creation
    mock_step_exec = MagicMock(spec=PipelineStepExecution)
    mock_step_exec.id = "test-step-execution-id"
    pipeline_engine.db.create_pipeline_step_execution = AsyncMock(return_value=mock_step_exec)
    
    # Mock step execution updating
    pipeline_engine.db.update_pipeline_step_execution = AsyncMock()
    pipeline_engine.db.complete_pipeline_step_execution = AsyncMock()
    pipeline_engine.db.complete_pipeline_execution = AsyncMock(return_value=mock_execution)
    
    # Mock the first step to succeed and the second to fail
    prompt_result = StepExecutionResult.success_result(
        outputs={"response": "Generated response text"}, 
        metrics={"tokens": 100}
    )
    transform_result = StepExecutionResult.error_result("Transformation failed")
    
    with patch.object(pipeline_engine, '_execute_prompt_step', return_value=prompt_result):
        with patch.object(pipeline_engine, '_execute_transform_step', return_value=transform_result):
            # Execute the pipeline
            result = await pipeline_engine.execute_pipeline(
                pipeline_id=mock_pipeline.id,
                user_id=mock_pipeline.user_id,
                input_parameters={"query": "Test query"}
            )
    
    # Verify the execution was marked as failed
    pipeline_engine.db.complete_pipeline_execution.assert_called_with(
        pipeline_engine.db,
        mock_execution.id,
        PipelineExecutionStatus.FAILED,
        error="Step execution failed: Process Response",
        results={"generated_text": "Generated response text"}
    )
    
    # The first step should have succeeded, the second failed
    assert pipeline_engine.db.complete_pipeline_step_execution.call_count == 2


@pytest.mark.asyncio
async def test_execute_step(pipeline_engine):
    """Tests executing a single pipeline step."""
    # Create a mock step
    mock_step = MagicMock(spec=PipelineStep)
    mock_step.id = "test-step-id"
    mock_step.name = "Test Step"
    mock_step.type = PipelineStepType.PROMPT.value
    mock_step.config = {"prompt": "Test prompt"}
    mock_step.input_mapping = None
    
    # Mock context
    context = {
        "input": {"query": "Test query"},
        "output": {},
        "pipeline_id": "test-pipeline-id",
        "user_id": "test-user-id",
        "execution_id": "test-execution-id"
    }
    
    # Mock step execution creation
    mock_step_exec = MagicMock(spec=PipelineStepExecution)
    mock_step_exec.id = "test-step-execution-id"
    pipeline_engine.db.create_pipeline_step_execution = AsyncMock(return_value=mock_step_exec)
    
    # Mock the handler
    expected_result = StepExecutionResult.success_result(
        outputs={"response": "Generated text"}, 
        metrics={"tokens": 50}
    )
    
    with patch.object(pipeline_engine, '_execute_prompt_step', return_value=expected_result):
        result = await pipeline_engine._execute_step(mock_step, context, "test-execution-id")
    
    # Verify result
    assert result.success
    assert result.outputs == expected_result.outputs
    assert result.metrics == expected_result.metrics
    
    # Verify step execution was created and completed
    pipeline_engine.db.create_pipeline_step_execution.assert_called_once()
    pipeline_engine.db.complete_pipeline_step_execution.assert_called_once()


@pytest.mark.asyncio
async def test_execute_step_error(pipeline_engine):
    """Tests executing a step that encounters an error."""
    # Create a mock step
    mock_step = MagicMock(spec=PipelineStep)
    mock_step.id = "test-step-id"
    mock_step.name = "Test Step"
    mock_step.type = PipelineStepType.PROMPT.value
    mock_step.config = {"prompt": "Test prompt"}
    mock_step.input_mapping = None
    
    # Mock context
    context = {
        "input": {"query": "Test query"},
        "output": {},
        "pipeline_id": "test-pipeline-id",
        "user_id": "test-user-id",
        "execution_id": "test-execution-id"
    }
    
    # Mock step execution creation
    mock_step_exec = MagicMock(spec=PipelineStepExecution)
    mock_step_exec.id = "test-step-execution-id"
    pipeline_engine.db.create_pipeline_step_execution = AsyncMock(return_value=mock_step_exec)
    
    # Mock the handler to raise an exception
    with patch.object(pipeline_engine, '_execute_prompt_step', side_effect=Exception("Test error")):
        result = await pipeline_engine._execute_step(mock_step, context, "test-execution-id")
    
    # Verify result indicates failure
    assert not result.success
    assert "Error in prompt step" in result.error
    
    # Verify step execution was created and marked as failed
    pipeline_engine.db.create_pipeline_step_execution.assert_called_once()
    pipeline_engine.db.complete_pipeline_step_execution.assert_called_once_with(
        pipeline_engine.db,
        mock_step_exec.id,
        PipelineStepExecutionStatus.FAILED,
        error="Error executing step Test Step: Test error",
        metrics={"duration_ms": pytest.approx(result.metrics["duration_ms"], abs=1000)}
    )


def test_resolve_step_inputs(pipeline_engine):
    """Tests resolving inputs for a step from the context."""
    # Create a mock step
    mock_step = MagicMock(spec=PipelineStep)
    mock_step.config = {"default_param": "default value"}
    mock_step.input_mapping = {
        "simple_param": "output.simple_value",
        "nested_param": "output.nested.value",
        "input_param": "input.query"
    }
    
    # Create a context
    context = {
        "input": {"query": "Test query"},
        "output": {
            "simple_value": "Simple value",
            "nested": {"value": "Nested value"}
        }
    }
    
    # Resolve inputs
    inputs = pipeline_engine._resolve_step_inputs(mock_step, context)
    
    # Verify resolved inputs
    assert inputs["default_param"] == "default value"
    assert inputs["simple_param"] == "Simple value"
    assert inputs["nested_param"] == "Nested value"
    assert inputs["input_param"] == "Test query"


def test_get_value_from_context(pipeline_engine):
    """Tests retrieving values from the context using a path."""
    # Create a context
    context = {
        "input": {"query": "Test query", "nested": {"value": "Nested input"}},
        "output": {
            "simple": "Simple output",
            "nested": {"value": "Nested output", "deep": {"value": "Deep output"}}
        }
    }
    
    # Test simple paths
    assert pipeline_engine._get_value_from_context("simple", context) == "Simple output"
    assert pipeline_engine._get_value_from_context({"source": "output", "path": "simple"}, context) == "Simple output"
    assert pipeline_engine._get_value_from_context({"source": "input", "path": "query"}, context) == "Test query"
    
    # Test nested paths
    assert pipeline_engine._get_value_from_context("nested.value", context) == "Nested output"
    assert pipeline_engine._get_value_from_context("nested.deep.value", context) == "Deep output"
    assert pipeline_engine._get_value_from_context({"source": "input", "path": "nested.value"}, context) == "Nested input"
    
    # Test missing paths
    assert pipeline_engine._get_value_from_context("missing", context) is None
    assert pipeline_engine._get_value_from_context("nested.missing", context) is None
    assert pipeline_engine._get_value_from_context("nested.deep.missing", context) is None