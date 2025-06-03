"""
Integration Tests for Pipeline Execution System.

These tests focus on the interaction between all components of the pipeline system,
including engine, database operations, and step execution.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
import json
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, func

from db.pipeline_models import (
    Pipeline, PipelineStep, PipelineExecution, PipelineStepExecution,
    PipelineExecutionStatus, PipelineStepExecutionStatus, PipelineStepType
)
from pipeline.engine import PipelineEngine, StepExecutionResult, PipelineExecutionError
import db.pipeline_crud as pipeline_crud


@pytest.fixture
async def db_session():
    """Creates a mock database session with configured pipeline entities."""
    db = AsyncMock(spec=AsyncSession)
    
    # Configure get_pipeline mock
    async def mock_get_pipeline(db, pipeline_id):
        pipeline = MagicMock(spec=Pipeline)
        pipeline.id = pipeline_id
        pipeline.name = "Test Pipeline"
        pipeline.user_id = "test-user"
        pipeline.is_public = False
        return pipeline
    
    # Configure get_pipeline_steps mock
    async def mock_get_pipeline_steps(db, pipeline_id, include_disabled=False):
        steps = []
        
        # Step 1: Prompt step
        prompt_step = MagicMock(spec=PipelineStep)
        prompt_step.id = f"{pipeline_id}-step1"
        prompt_step.name = "Generate Content"
        prompt_step.type = PipelineStepType.PROMPT.value
        prompt_step.order = 1
        prompt_step.config = {
            "model_id": "test-model",
            "prompt": "Generate content about {{input.topic}}"
        }
        prompt_step.input_mapping = {
            "prompt": "input.topic"
        }
        steps.append(prompt_step)
        
        # Step 2: Transform step
        transform_step = MagicMock(spec=PipelineStep)
        transform_step.id = f"{pipeline_id}-step2"
        transform_step.name = "Process Content"
        transform_step.type = PipelineStepType.TRANSFORM.value
        transform_step.order = 2
        transform_step.config = {
            "transform_type": "text_to_json"
        }
        transform_step.input_mapping = {
            "data": "output.response"
        }
        steps.append(transform_step)
        
        return steps
    
    # Configure create_pipeline_execution mock
    async def mock_create_pipeline_execution(db, pipeline_id, user_id, input_parameters=None):
        execution = MagicMock(spec=PipelineExecution)
        execution.id = f"exec-{uuid.uuid4()}"
        execution.pipeline_id = pipeline_id
        execution.user_id = user_id
        execution.status = PipelineExecutionStatus.PENDING.value
        execution.started_at = datetime.now()
        execution.input_parameters = input_parameters or {}
        return execution
    
    # Configure create_pipeline_step_execution mock
    async def mock_create_pipeline_step_execution(
        db, pipeline_execution_id, step_id, inputs=None, model_id=None
    ):
        step_execution = MagicMock(spec=PipelineStepExecution)
        step_execution.id = f"step-exec-{uuid.uuid4()}"
        step_execution.pipeline_execution_id = pipeline_execution_id
        step_execution.step_id = step_id
        step_execution.status = PipelineStepExecutionStatus.PENDING.value
        step_execution.started_at = datetime.now()
        step_execution.inputs = inputs or {}
        step_execution.model_id = model_id
        return step_execution
    
    # Configure update mocks
    async def mock_update_pipeline_execution(db, execution_id, data):
        # This would update the execution in the database
        pass
    
    async def mock_update_pipeline_step_execution(db, step_execution_id, data):
        # This would update the step execution in the database
        pass
    
    async def mock_complete_pipeline_execution(
        db, execution_id, status, results=None, error=None
    ):
        execution = MagicMock(spec=PipelineExecution)
        execution.id = execution_id
        execution.status = status.value
        execution.completed_at = datetime.now()
        execution.results = results
        execution.error = error
        return execution
    
    async def mock_complete_pipeline_step_execution(
        db, step_execution_id, status, outputs=None, error=None, metrics=None
    ):
        step_execution = MagicMock(spec=PipelineStepExecution)
        step_execution.id = step_execution_id
        step_execution.status = status.value
        step_execution.completed_at = datetime.now()
        step_execution.outputs = outputs
        step_execution.error = error
        step_execution.metrics = metrics
        return step_execution
    
    # Patch the pipeline CRUD functions
    with patch('db.pipeline_crud.get_pipeline', side_effect=mock_get_pipeline), \
         patch('db.pipeline_crud.get_pipeline_steps', side_effect=mock_get_pipeline_steps), \
         patch('db.pipeline_crud.create_pipeline_execution', side_effect=mock_create_pipeline_execution), \
         patch('db.pipeline_crud.create_pipeline_step_execution', side_effect=mock_create_pipeline_step_execution), \
         patch('db.pipeline_crud.update_pipeline_execution', side_effect=mock_update_pipeline_execution), \
         patch('db.pipeline_crud.update_pipeline_step_execution', side_effect=mock_update_pipeline_step_execution), \
         patch('db.pipeline_crud.complete_pipeline_execution', side_effect=mock_complete_pipeline_execution), \
         patch('db.pipeline_crud.complete_pipeline_step_execution', side_effect=mock_complete_pipeline_step_execution):
        
        yield db


@pytest.fixture
def pipeline_engine(db_session):
    """Creates a PipelineEngine with the mock database session."""
    return PipelineEngine(db_session)


@pytest.mark.asyncio
async def test_full_pipeline_execution(pipeline_engine):
    """
    Tests the full pipeline execution flow, from start to finish.
    
    This test verifies:
    1. Pipeline retrieval
    2. Step retrieval
    3. Execution creation
    4. Step execution and sequential processing
    5. Context management
    6. Final results
    """
    # Mock the model retrieval
    model = MagicMock()
    model.id = "test-model"
    pipeline_engine.db.get_model = AsyncMock(return_value=model)
    
    # Mock the step execution handlers
    # Step 1: Prompt step result
    prompt_result = StepExecutionResult.success_result(
        outputs={
            "response": "Generated content about testing.",
            "model_id": "test-model"
        },
        metrics={"tokens": 120}
    )
    
    # Step 2: Transform step result
    transform_result = StepExecutionResult.success_result(
        outputs={
            "result": {"content": "Generated content about testing.", "type": "test"}
        }
    )
    
    # Mock the step execution handlers
    with patch.object(pipeline_engine, '_execute_prompt_step', return_value=prompt_result), \
         patch.object(pipeline_engine, '_execute_transform_step', return_value=transform_result):
        
        # Execute the pipeline
        result = await pipeline_engine.execute_pipeline(
            pipeline_id="test-pipeline",
            user_id="test-user",
            input_parameters={"topic": "testing"}
        )
    
    # Check that the pipeline was successfully executed
    assert result is not None
    assert result.status == PipelineExecutionStatus.COMPLETED.value
    
    # Check that the final results contain the expected outputs
    assert result.results is not None
    assert "response" in result.results
    assert "result" in result.results
    assert result.results["response"] == "Generated content about testing."
    assert result.results["result"]["content"] == "Generated content about testing."


@pytest.mark.asyncio
async def test_pipeline_execution_with_error(pipeline_engine):
    """
    Tests pipeline execution that encounters an error in one of its steps.
    
    This test verifies:
    1. Error handling in step execution
    2. Proper status updates
    3. Error reporting in execution results
    """
    # Mock the model retrieval
    model = MagicMock()
    model.id = "test-model"
    pipeline_engine.db.get_model = AsyncMock(return_value=model)
    
    # Mock the step execution handlers
    # Step 1: Prompt step succeeds
    prompt_result = StepExecutionResult.success_result(
        outputs={
            "response": "Generated content about testing.",
            "model_id": "test-model"
        }
    )
    
    # Step 2: Transform step fails
    transform_result = StepExecutionResult.error_result(
        "Failed to transform content: Invalid JSON format"
    )
    
    # Mock the step execution handlers
    with patch.object(pipeline_engine, '_execute_prompt_step', return_value=prompt_result), \
         patch.object(pipeline_engine, '_execute_transform_step', return_value=transform_result):
        
        # Execute the pipeline
        result = await pipeline_engine.execute_pipeline(
            pipeline_id="test-pipeline",
            user_id="test-user",
            input_parameters={"topic": "testing"}
        )
    
    # Check that the pipeline was marked as failed
    assert result is not None
    assert result.status == PipelineExecutionStatus.FAILED.value
    
    # Check that the error message is included
    assert result.error is not None
    assert "Process Content" in result.error
    
    # Check that partial results (from successful steps) are included
    assert result.results is not None
    assert "response" in result.results
    assert result.results["response"] == "Generated content about testing."


@pytest.mark.asyncio
async def test_pipeline_execution_with_custom_handlers(db_session):
    """
    Tests pipeline execution with custom step handlers.
    
    This test verifies:
    1. Registration of custom step handlers
    2. Custom handler execution
    3. Custom handler integration with pipeline flow
    """
    # Create a pipeline engine
    engine = PipelineEngine(db_session)
    
    # Define a custom step type and handler
    custom_step_type = "custom_analyzer"
    
    # Custom step handler
    async def custom_analyzer_handler(step, inputs, context):
        # Process the inputs according to custom logic
        if "text" not in inputs:
            return StepExecutionResult.error_result("Missing required input 'text'")
        
        # Perform custom analysis
        text = inputs["text"]
        word_count = len(text.split())
        char_count = len(text)
        
        # Return results
        return StepExecutionResult.success_result(
            outputs={
                "analysis": {
                    "word_count": word_count,
                    "char_count": char_count,
                    "avg_word_length": char_count / word_count if word_count > 0 else 0
                },
                "input_text": text
            }
        )
    
    # Register the custom handler
    engine.register_step_handler(custom_step_type, custom_analyzer_handler)
    
    # Mock get_pipeline to return a pipeline with a custom step
    async def mock_get_pipeline(db, pipeline_id):
        pipeline = MagicMock(spec=Pipeline)
        pipeline.id = pipeline_id
        pipeline.name = "Custom Pipeline"
        pipeline.user_id = "test-user"
        pipeline.is_public = False
        return pipeline
    
    # Mock get_pipeline_steps to include custom step
    async def mock_get_pipeline_steps(db, pipeline_id, include_disabled=False):
        steps = []
        
        # Step 1: Prompt step
        prompt_step = MagicMock(spec=PipelineStep)
        prompt_step.id = f"{pipeline_id}-step1"
        prompt_step.name = "Generate Text"
        prompt_step.type = PipelineStepType.PROMPT.value
        prompt_step.order = 1
        prompt_step.config = {
            "model_id": "test-model",
            "prompt": "Generate a paragraph about {{input.topic}}"
        }
        prompt_step.input_mapping = {
            "prompt": "input.topic"
        }
        steps.append(prompt_step)
        
        # Step 2: Custom analyzer step
        custom_step = MagicMock(spec=PipelineStep)
        custom_step.id = f"{pipeline_id}-step2"
        custom_step.name = "Analyze Text"
        custom_step.type = custom_step_type
        custom_step.order = 2
        custom_step.config = {}
        custom_step.input_mapping = {
            "text": "output.response"
        }
        steps.append(custom_step)
        
        return steps
    
    # Patch the pipeline CRUD functions
    with patch('db.pipeline_crud.get_pipeline', side_effect=mock_get_pipeline), \
         patch('db.pipeline_crud.get_pipeline_steps', side_effect=mock_get_pipeline_steps):
        
        # Mock the model retrieval
        model = MagicMock()
        model.id = "test-model"
        engine.db.get_model = AsyncMock(return_value=model)
        
        # Mock the prompt step handler
        prompt_result = StepExecutionResult.success_result(
            outputs={
                "response": "This is a generated paragraph about custom pipeline steps. It contains multiple words and characters for analysis.",
                "model_id": "test-model"
            }
        )
        
        with patch.object(engine, '_execute_prompt_step', return_value=prompt_result):
            # Execute the pipeline
            result = await engine.execute_pipeline(
                pipeline_id="custom-pipeline",
                user_id="test-user",
                input_parameters={"topic": "custom pipeline steps"}
            )
    
    # Check that the pipeline was successfully executed
    assert result is not None
    assert result.status == PipelineExecutionStatus.COMPLETED.value
    
    # Check that the results include both prompt and custom analyzer outputs
    assert result.results is not None
    assert "response" in result.results
    assert "analysis" in result.results
    
    # Verify custom analyzer results
    assert result.results["analysis"]["word_count"] > 0
    assert result.results["analysis"]["char_count"] > 0
    assert result.results["analysis"]["avg_word_length"] > 0


@pytest.mark.asyncio
async def test_pipeline_with_authorization(pipeline_engine):
    """
    Tests pipeline execution authorization rules.
    
    This test verifies:
    1. Private pipeline execution by owner
    2. Private pipeline execution rejection for non-owners
    3. Public pipeline execution by non-owners
    """
    # Create a test pipeline
    pipeline_id = "auth-test-pipeline"
    owner_id = "pipeline-owner"
    non_owner_id = "other-user"
    
    # Mock get_pipeline with configurable user and publicity
    def create_pipeline_mock(user_id, is_public):
        pipeline = MagicMock(spec=Pipeline)
        pipeline.id = pipeline_id
        pipeline.name = "Auth Test Pipeline"
        pipeline.user_id = user_id
        pipeline.is_public = is_public
        return pipeline
    
    # Test 1: Owner can execute private pipeline
    with patch('db.pipeline_crud.get_pipeline', return_value=create_pipeline_mock(owner_id, False)):
        # Should succeed (owner accessing private pipeline)
        try:
            # We'll patch the rest of the execution to raise a controlled exception
            # after authorization succeeds
            with patch('db.pipeline_crud.get_pipeline_steps', side_effect=ValueError("Test stop")):
                with pytest.raises(ValueError, match="Test stop"):
                    await pipeline_engine.execute_pipeline(
                        pipeline_id=pipeline_id,
                        user_id=owner_id,
                        input_parameters={}
                    )
        except PipelineExecutionError as e:
            assert False, f"Owner was not authorized: {str(e)}"
    
    # Test 2: Non-owner cannot execute private pipeline
    with patch('db.pipeline_crud.get_pipeline', return_value=create_pipeline_mock(owner_id, False)):
        # Should fail (non-owner accessing private pipeline)
        with pytest.raises(PipelineExecutionError) as excinfo:
            await pipeline_engine.execute_pipeline(
                pipeline_id=pipeline_id,
                user_id=non_owner_id,
                input_parameters={}
            )
        assert "Not authorized" in str(excinfo.value)
    
    # Test 3: Non-owner can execute public pipeline
    with patch('db.pipeline_crud.get_pipeline', return_value=create_pipeline_mock(owner_id, True)):
        # Should succeed (non-owner accessing public pipeline)
        try:
            # We'll patch the rest of the execution to raise a controlled exception
            # after authorization succeeds
            with patch('db.pipeline_crud.get_pipeline_steps', side_effect=ValueError("Test stop")):
                with pytest.raises(ValueError, match="Test stop"):
                    await pipeline_engine.execute_pipeline(
                        pipeline_id=pipeline_id,
                        user_id=non_owner_id,
                        input_parameters={}
                    )
        except PipelineExecutionError as e:
            assert False, f"Non-owner was not authorized for public pipeline: {str(e)}"