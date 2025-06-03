"""
Tests for Pipeline Execution Engine functionality.

These tests focus on the full execution flow of pipelines with different step types
and configurations, ensuring proper data flow, error handling, and state management.
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


@pytest.fixture
def multi_step_pipeline():
    """Creates a mock multi-step pipeline with different step types."""
    pipeline = MagicMock(spec=Pipeline)
    pipeline.id = "multi-step-pipeline"
    pipeline.name = "Multi-Step Pipeline"
    pipeline.user_id = "test-user"
    pipeline.is_public = False
    
    # Create steps with different types
    steps = []
    
    # Step 1: Prompt step
    prompt_step = MagicMock(spec=PipelineStep)
    prompt_step.id = "step1"
    prompt_step.name = "Initial Prompt"
    prompt_step.type = PipelineStepType.PROMPT.value
    prompt_step.order = 1
    prompt_step.config = {
        "model_id": "test-model",
        "prompt": "Generate initial content based on {{input.topic}}"
    }
    prompt_step.input_mapping = {
        "prompt": "input.topic"
    }
    steps.append(prompt_step)
    
    # Step 2: Transform step
    transform_step = MagicMock(spec=PipelineStep)
    transform_step.id = "step2"
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
    
    # Step 3: Code step
    code_step = MagicMock(spec=PipelineStep)
    code_step.id = "step3"
    code_step.name = "Process Data"
    code_step.type = PipelineStepType.CODE.value
    code_step.order = 3
    code_step.config = {
        "language": "python",
        "code": "import json\nresult = {'processed': input_data, 'count': len(input_data)}\nprint(json.dumps(result))"
    }
    code_step.input_mapping = {
        "input_data": "output.result.parsed"
    }
    steps.append(code_step)
    
    # Step 4: Condition step
    condition_step = MagicMock(spec=PipelineStep)
    condition_step.id = "step4"
    condition_step.name = "Check Results"
    condition_step.type = PipelineStepType.CONDITION.value
    condition_step.order = 4
    condition_step.config = {
        "condition": "output.processed.count > 10"
    }
    condition_step.input_mapping = {
        "condition": "output.result.count > 10"
    }
    steps.append(condition_step)
    
    # Step 5: File step (writes to file)
    file_step = MagicMock(spec=PipelineStep)
    file_step.id = "step5"
    file_step.name = "Save Results"
    file_step.type = PipelineStepType.FILE.value
    file_step.order = 5
    file_step.config = {
        "operation": "write",
        "file_path": "test-output.json"
    }
    file_step.input_mapping = {
        "content": "output.result"
    }
    steps.append(file_step)
    
    return pipeline, steps


@pytest.mark.asyncio
async def test_multi_step_pipeline_execution(pipeline_engine, multi_step_pipeline):
    """Tests execution of a pipeline with multiple step types."""
    pipeline, steps = multi_step_pipeline
    
    # Mock database calls
    pipeline_engine.db.get_pipeline = AsyncMock(return_value=pipeline)
    pipeline_engine.db.get_pipeline_steps = AsyncMock(return_value=steps)
    
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
    pipeline_engine.db.append_step_execution_log = AsyncMock(return_value=True)
    
    # Mock step handlers
    # Step 1: Prompt handler
    prompt_result = StepExecutionResult.success_result(
        outputs={
            "response": "Generated text about testing",
            "model_id": "test-model"
        },
        metrics={"tokens": 100}
    )
    
    # Step 2: Transform handler
    transform_result = StepExecutionResult.success_result(
        outputs={
            "result": {"parsed": "Generated text about testing"}
        }
    )
    
    # Step 3: Code handler
    code_result = StepExecutionResult.success_result(
        outputs={
            "result": {
                "processed": "Generated text about testing", 
                "count": 15
            },
            "stdout": json.dumps({
                "processed": "Generated text about testing", 
                "count": 15
            }),
            "stderr": "",
            "return_code": 0
        }
    )
    
    # Step 4: Condition handler
    condition_result = StepExecutionResult.success_result(
        outputs={"result": True, "condition": "count > 10"}
    )
    
    # Step 5: File handler
    file_result = StepExecutionResult.success_result(
        outputs={
            "written": True,
            "path": "test-output.json",
            "size": 100
        }
    )
    
    # Patch all step handlers
    with patch.object(pipeline_engine, '_execute_prompt_step', return_value=prompt_result), \
         patch.object(pipeline_engine, '_execute_transform_step', return_value=transform_result), \
         patch.object(pipeline_engine, '_execute_code_step', return_value=code_result), \
         patch.object(pipeline_engine, '_execute_condition_step', return_value=condition_result), \
         patch.object(pipeline_engine, '_execute_file_step', return_value=file_result):
        
        # Execute the pipeline
        result = await pipeline_engine.execute_pipeline(
            pipeline_id=pipeline.id,
            user_id=pipeline.user_id,
            input_parameters={"topic": "Testing pipelines"}
        )
    
    # Verify the execution was created and completed
    pipeline_engine.db.create_pipeline_execution.assert_called_once()
    
    # Each step should have been executed (5 steps)
    assert pipeline_engine.db.create_pipeline_step_execution.call_count == 5
    assert pipeline_engine.db.complete_pipeline_step_execution.call_count == 5
    
    # Final execution should be marked as completed with all step outputs
    pipeline_engine.db.complete_pipeline_execution.assert_called_with(
        pipeline_engine.db,
        mock_execution.id,
        PipelineExecutionStatus.COMPLETED,
        results=pytest.approx({
            "response": "Generated text about testing",
            "result": {
                "parsed": "Generated text about testing"
            },
            "processed": "Generated text about testing",
            "count": 15,
            "written": True,
            "path": "test-output.json",
            "size": 100
        }, abs=1e-10)
    )


@pytest.mark.asyncio
async def test_pipeline_with_step_error(pipeline_engine, multi_step_pipeline):
    """Tests handling of errors during pipeline execution."""
    pipeline, steps = multi_step_pipeline
    
    # Mock database calls
    pipeline_engine.db.get_pipeline = AsyncMock(return_value=pipeline)
    pipeline_engine.db.get_pipeline_steps = AsyncMock(return_value=steps)
    
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
    
    # Mock step handlers - make the code step fail
    prompt_result = StepExecutionResult.success_result(
        outputs={"response": "Generated text about testing"}
    )
    
    transform_result = StepExecutionResult.success_result(
        outputs={"result": {"parsed": "Generated text about testing"}}
    )
    
    # This step will fail
    code_result = StepExecutionResult.error_result(
        "Runtime error: Variable 'input_data' is not defined",
        outputs={"stderr": "NameError: name 'input_data' is not defined"}
    )
    
    # These steps won't be reached
    condition_result = StepExecutionResult.success_result(
        outputs={"result": True}
    )
    
    file_result = StepExecutionResult.success_result(
        outputs={"written": True}
    )
    
    # Patch all step handlers
    with patch.object(pipeline_engine, '_execute_prompt_step', return_value=prompt_result), \
         patch.object(pipeline_engine, '_execute_transform_step', return_value=transform_result), \
         patch.object(pipeline_engine, '_execute_code_step', return_value=code_result), \
         patch.object(pipeline_engine, '_execute_condition_step', return_value=condition_result), \
         patch.object(pipeline_engine, '_execute_file_step', return_value=file_result):
        
        # Execute the pipeline
        result = await pipeline_engine.execute_pipeline(
            pipeline_id=pipeline.id,
            user_id=pipeline.user_id,
            input_parameters={"topic": "Testing pipelines"}
        )
    
    # Verify only the first three steps were executed (the third one failed)
    assert pipeline_engine.db.create_pipeline_step_execution.call_count == 3
    assert pipeline_engine.db.complete_pipeline_step_execution.call_count == 3
    
    # Final execution should be marked as failed
    pipeline_engine.db.complete_pipeline_execution.assert_called_with(
        pipeline_engine.db,
        mock_execution.id,
        PipelineExecutionStatus.FAILED,
        error="Step execution failed: Process Data",
        results={"response": "Generated text about testing", "result": {"parsed": "Generated text about testing"}}
    )


@pytest.mark.asyncio
async def test_pipeline_execution_unauthorized(pipeline_engine, multi_step_pipeline):
    """Tests attempting to execute a pipeline without authorization."""
    pipeline, steps = multi_step_pipeline
    
    # Mock database calls
    pipeline_engine.db.get_pipeline = AsyncMock(return_value=pipeline)
    
    # Try to execute the pipeline with a different user ID
    with pytest.raises(PipelineExecutionError) as excinfo:
        await pipeline_engine.execute_pipeline(
            pipeline_id=pipeline.id,
            user_id="unauthorized-user",
            input_parameters={"topic": "Testing pipelines"}
        )
    
    assert "Not authorized" in str(excinfo.value)
    
    # Make the pipeline public and verify it works with a different user
    pipeline.is_public = True
    pipeline_engine.db.get_pipeline_steps = AsyncMock(return_value=steps)
    
    # Mock execution creation
    mock_execution = MagicMock(spec=PipelineExecution)
    mock_execution.id = "test-execution-id"
    pipeline_engine.db.create_pipeline_execution = AsyncMock(return_value=mock_execution)
    
    # Mock step execution with all success results
    pipeline_engine.db.create_pipeline_step_execution = AsyncMock()
    pipeline_engine.db.update_pipeline_step_execution = AsyncMock()
    pipeline_engine.db.complete_pipeline_step_execution = AsyncMock()
    pipeline_engine.db.complete_pipeline_execution = AsyncMock(return_value=mock_execution)
    
    # Mock all step handlers to return success
    success_result = StepExecutionResult.success_result(outputs={})
    with patch.object(pipeline_engine, '_execute_step', return_value=success_result):
        result = await pipeline_engine.execute_pipeline(
            pipeline_id=pipeline.id,
            user_id="authorized-public-user",
            input_parameters={"topic": "Testing pipelines"}
        )
    
    # Execution should be created for the public user
    pipeline_engine.db.create_pipeline_execution.assert_called_with(
        pipeline_engine.db,
        pipeline.id,
        "authorized-public-user",
        {"topic": "Testing pipelines"}
    )


@pytest.mark.asyncio
async def test_pipeline_with_missing_steps(pipeline_engine, multi_step_pipeline):
    """Tests handling of a pipeline with no enabled steps."""
    pipeline, _ = multi_step_pipeline
    
    # Mock database calls
    pipeline_engine.db.get_pipeline = AsyncMock(return_value=pipeline)
    pipeline_engine.db.get_pipeline_steps = AsyncMock(return_value=[])  # No steps
    
    # Try to execute the pipeline
    with pytest.raises(PipelineExecutionError) as excinfo:
        await pipeline_engine.execute_pipeline(
            pipeline_id=pipeline.id,
            user_id=pipeline.user_id,
            input_parameters={"topic": "Testing pipelines"}
        )
    
    assert "no enabled steps" in str(excinfo.value)


@pytest.mark.asyncio
async def test_complex_input_output_mapping(pipeline_engine):
    """Tests complex input/output mapping between pipeline steps."""
    # Create a pipeline with complex input/output mapping
    pipeline = MagicMock(spec=Pipeline)
    pipeline.id = "complex-mapping-pipeline"
    pipeline.name = "Complex Mapping Pipeline"
    pipeline.user_id = "test-user"
    pipeline.is_public = False
    
    # Create steps with complex mappings
    steps = []
    
    # Step 1: Generates nested output
    step1 = MagicMock(spec=PipelineStep)
    step1.id = "step1"
    step1.name = "Generate Data"
    step1.type = PipelineStepType.CODE.value
    step1.order = 1
    step1.config = {
        "language": "python",
        "code": """
import json
data = {
    "level1": {
        "level2": {
            "level3": "nested value",
            "array": [1, 2, 3, 4, 5]
        },
        "sibling": "sibling value"
    },
    "top_level": "top value"
}
print(json.dumps(data))
"""
    }
    step1.input_mapping = {}
    step1.output_mapping = {
        "structured_data": "result"
    }
    steps.append(step1)
    
    # Step 2: Uses deep nested values from step 1
    step2 = MagicMock(spec=PipelineStep)
    step2.id = "step2"
    step2.name = "Process Nested Data"
    step2.type = PipelineStepType.CODE.value
    step2.order = 2
    step2.config = {
        "language": "python",
        "code": """
import json
nested_value = params['nested_value']
sibling_value = params['sibling_value']
top_value = params['top_value']
array = params['array']

result = {
    "values": {
        "nested": nested_value,
        "sibling": sibling_value,
        "top": top_value
    },
    "array_sum": sum(array)
}
print(json.dumps(result))
"""
    }
    step2.input_mapping = {
        "params": {
            "nested_value": "output.structured_data.level1.level2.level3",
            "sibling_value": "output.structured_data.level1.sibling",
            "top_value": "output.structured_data.top_level",
            "array": "output.structured_data.level1.level2.array"
        }
    }
    steps.append(step2)
    
    # Mock database calls
    pipeline_engine.db.get_pipeline = AsyncMock(return_value=pipeline)
    pipeline_engine.db.get_pipeline_steps = AsyncMock(return_value=steps)
    
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
    
    # Mock step results
    step1_result = StepExecutionResult.success_result(
        outputs={
            "result": {
                "level1": {
                    "level2": {
                        "level3": "nested value",
                        "array": [1, 2, 3, 4, 5]
                    },
                    "sibling": "sibling value"
                },
                "top_level": "top value"
            },
            "stdout": '{"level1": {"level2": {"level3": "nested value", "array": [1, 2, 3, 4, 5]}, "sibling": "sibling value"}, "top_level": "top value"}',
            "stderr": "",
            "return_code": 0
        }
    )
    
    step2_result = StepExecutionResult.success_result(
        outputs={
            "result": {
                "values": {
                    "nested": "nested value",
                    "sibling": "sibling value",
                    "top": "top value"
                },
                "array_sum": 15
            },
            "stdout": '{"values": {"nested": "nested value", "sibling": "sibling value", "top": "top value"}, "array_sum": 15}',
            "stderr": "",
            "return_code": 0
        }
    )
    
    # Execute with mocked steps
    with patch.object(pipeline_engine, '_execute_code_step', side_effect=[step1_result, step2_result]):
        result = await pipeline_engine.execute_pipeline(
            pipeline_id=pipeline.id,
            user_id=pipeline.user_id,
            input_parameters={}
        )
    
    # Verify both steps executed and the pipeline completed
    assert pipeline_engine.db.create_pipeline_step_execution.call_count == 2
    assert pipeline_engine.db.complete_pipeline_step_execution.call_count == 2
    
    # Check that the final context contains the merged outputs
    pipeline_engine.db.complete_pipeline_execution.assert_called_with(
        pipeline_engine.db,
        mock_execution.id,
        PipelineExecutionStatus.COMPLETED,
        results=pytest.approx({
            "structured_data": {
                "level1": {
                    "level2": {
                        "level3": "nested value",
                        "array": [1, 2, 3, 4, 5]
                    },
                    "sibling": "sibling value"
                },
                "top_level": "top value"
            },
            "result": {
                "values": {
                    "nested": "nested value",
                    "sibling": "sibling value",
                    "top": "top value"
                },
                "array_sum": 15
            }
        }, abs=1e-10)
    )


@pytest.mark.asyncio
async def test_prompt_step_execution(pipeline_engine):
    """Tests the prompt step handler for API calls to LLM models."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "test-prompt-step"
    step.name = "Test Prompt"
    step.type = PipelineStepType.PROMPT.value
    step.config = {
        "model_id": "test-model-chat",
        "prompt": "Generate a test response",
        "system_prompt": "You are a test assistant"
    }
    
    # Mock inputs already resolved from context
    inputs = {
        "model_id": "test-model-chat",
        "prompt": "Generate a test response",
        "system_prompt": "You are a test assistant",
        "options": {"temperature": 0.7}
    }
    
    # Create execution context
    context = {
        "step_execution_id": "test-step-exec-id",
        "pipeline_execution_id": "test-pipeline-exec-id",
        "pipeline_id": "test-pipeline-id",
        "user_id": "test-user-id"
    }
    
    # Mock DB operations
    pipeline_engine.db.get_model = AsyncMock(return_value=MagicMock())
    
    # Mock the HTTP client and app state
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "message": {
            "content": "This is a test response from the model."
        },
        "prompt_eval_count": 20,
        "eval_count": 30
    }
    
    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    
    # Mock main app with HTTP client
    with patch('pipeline.engine.main') as mock_main:
        mock_main.app.state.http_client = mock_client
        
        # Execute the prompt step
        result = await pipeline_engine._execute_prompt_step(step, inputs, context)
    
    # Verify HTTP call was made to chat endpoint
    mock_client.post.assert_called_once()
    args, kwargs = mock_client.post.call_args
    assert args[0] == "/api/chat"
    assert kwargs["json"]["model"] == "test-model-chat"
    assert kwargs["json"]["messages"] == [
        {"role": "system", "content": "You are a test assistant"},
        {"role": "user", "content": "Generate a test response"}
    ]
    assert kwargs["json"]["options"] == {"temperature": 0.7}
    
    # Check the result
    assert result.success
    assert result.outputs["response"] == "This is a test response from the model."
    assert result.outputs["model_id"] == "test-model-chat"
    
    # Check metrics were tracked
    assert result.metrics["tokens_prompt"] == 20
    assert result.metrics["tokens_completion"] == 30
    assert result.metrics["tokens_total"] == 50


@pytest.mark.asyncio
async def test_code_step_execution(pipeline_engine):
    """Tests the code step handler that executes a code snippet."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "test-code-step"
    step.name = "Test Code"
    step.type = PipelineStepType.CODE.value
    step.config = {
        "language": "python",
        "code": "import json\nresult = {'hello': 'world', 'value': 42}\nprint(json.dumps(result))"
    }
    
    # Mock inputs already resolved from context
    inputs = {
        "language": "python",
        "code": "import json\nresult = {'hello': 'world', 'value': 42}\nprint(json.dumps(result))",
        "timeout": 5
    }
    
    # Create execution context
    context = {
        "step_execution_id": "test-step-exec-id",
        "pipeline_execution_id": "test-pipeline-exec-id",
        "pipeline_id": "test-pipeline-id",
        "user_id": "test-user-id"
    }
    
    # Create a subprocess mock for the code execution
    mock_process = AsyncMock()
    mock_process.returncode = 0
    mock_process.communicate = AsyncMock(return_value=(
        b'{"hello": "world", "value": 42}',  # stdout
        b''  # stderr
    ))
    
    # Execute with mocked process
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        result = await pipeline_engine._execute_code_step(step, inputs, context)
    
    # Check the result
    assert result.success
    assert result.outputs["stdout"] == '{"hello": "world", "value": 42}'
    assert result.outputs["stderr"] == ''
    assert result.outputs["return_code"] == 0
    assert result.outputs["success"] is True
    assert result.outputs["parsed_output"] == {"hello": "world", "value": 42}
    assert result.outputs["result"] == {"hello": "world", "value": 42}


@pytest.mark.asyncio
async def test_code_step_execution_error(pipeline_engine):
    """Tests the code step handler with an execution error."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "test-code-step-error"
    step.name = "Test Code Error"
    step.type = PipelineStepType.CODE.value
    step.config = {
        "language": "python",
        "code": "import json\nraise ValueError('Test error')"
    }
    
    # Mock inputs already resolved from context
    inputs = {
        "language": "python",
        "code": "import json\nraise ValueError('Test error')",
        "timeout": 5
    }
    
    # Create execution context
    context = {
        "step_execution_id": "test-step-exec-id",
        "pipeline_execution_id": "test-pipeline-exec-id",
        "pipeline_id": "test-pipeline-id",
        "user_id": "test-user-id"
    }
    
    # Create a subprocess mock for the code execution
    mock_process = AsyncMock()
    mock_process.returncode = 1
    mock_process.communicate = AsyncMock(return_value=(
        b'',  # stdout
        b'Traceback (most recent call last):\n  File "temp.py", line 2, in <module>\n    raise ValueError(\'Test error\')\nValueError: Test error'  # stderr
    ))
    
    # Execute with mocked process
    with patch('asyncio.create_subprocess_exec', return_value=mock_process):
        result = await pipeline_engine._execute_code_step(step, inputs, context)
    
    # Check the result indicates failure
    assert not result.success
    assert result.outputs["stdout"] == ''
    assert "ValueError: Test error" in result.outputs["stderr"]
    assert result.outputs["return_code"] == 1
    assert result.outputs["success"] is False
    assert result.error is not None


@pytest.mark.asyncio
async def test_file_step_execution(pipeline_engine):
    """Tests the file step handler that reads/writes files."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "test-file-step"
    step.name = "Test File"
    step.type = PipelineStepType.FILE.value
    step.config = {
        "operation": "write",
        "file_path": "test-file.json"
    }
    
    # Mock inputs already resolved from context
    inputs = {
        "operation": "write",
        "file_path": "/tmp/test-file.json",
        "content": {"test": "data", "value": 42}
    }
    
    # Create execution context
    context = {
        "step_execution_id": "test-step-exec-id",
        "pipeline_execution_id": "test-pipeline-exec-id",
        "pipeline_id": "test-pipeline-id",
        "user_id": "test-user-id"
    }
    
    # Mock aiofiles and os operations
    mock_file = AsyncMock()
    mock_file.__aenter__ = AsyncMock(return_value=mock_file)
    mock_file.__aexit__ = AsyncMock(return_value=False)
    mock_file.write = AsyncMock()
    
    with patch('pipeline.engine.main') as mock_main, \
         patch('pipeline.engine.aiofiles.open', return_value=mock_file), \
         patch('pipeline.engine.os.path.abspath', return_value="/uploads/test-file.json"), \
         patch('pipeline.engine.os.makedirs'), \
         patch('pipeline.engine.os.stat') as mock_stat:
        
        # Mock the uploads directory setting
        mock_main.settings.upload_dir = "/uploads"
        
        # Mock os.stat for file metadata
        mock_stat_result = MagicMock()
        mock_stat_result.st_size = 100
        mock_stat_result.st_mtime = 1613545200.0
        mock_stat_result.st_ctime = 1613545200.0
        mock_stat.return_value = mock_stat_result
        
        # Execute the file step
        result = await pipeline_engine._execute_file_step(step, inputs, context)
    
    # Check the result
    assert result.success
    assert result.outputs["written"] is True
    assert "/uploads/test-file.json" in result.outputs["path"]
    assert result.outputs["size"] == 100
    
    # Verify file was created at the right path
    mock_file.write.assert_called_once()
    write_content = mock_file.write.call_args[0][0]
    assert "test" in write_content
    assert "42" in write_content


@pytest.mark.asyncio
async def test_api_step_execution(pipeline_engine):
    """Tests the API step handler that makes HTTP requests."""
    # Create a mock step
    step = MagicMock(spec=PipelineStep)
    step.id = "test-api-step"
    step.name = "Test API"
    step.type = PipelineStepType.API.value
    step.config = {
        "method": "GET",
        "url": "https://api.example.com/data"
    }
    
    # Mock inputs already resolved from context
    inputs = {
        "method": "GET",
        "url": "https://api.example.com/data",
        "headers": {"Accept": "application/json"},
        "params": {"query": "test"}
    }
    
    # Create execution context
    context = {
        "step_execution_id": "test-step-exec-id",
        "pipeline_execution_id": "test-pipeline-exec-id",
        "pipeline_id": "test-pipeline-id",
        "user_id": "test-user-id"
    }
    
    # Mock HTTP client response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.elapsed.total_seconds.return_value = 0.5
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.content = b'{"success": true, "data": {"id": 123, "name": "Test"}}'
    mock_response.text = '{"success": true, "data": {"id": 123, "name": "Test"}}'
    mock_response.json.return_value = {"success": True, "data": {"id": 123, "name": "Test"}}
    
    # Mock HTTP client
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_response)
    
    # Execute the API step
    with patch('pipeline.engine.httpx.AsyncClient', return_value=mock_client):
        result = await pipeline_engine._execute_api_step(step, inputs, context)
    
    # Check the result
    assert result.success
    assert result.outputs["status"] == 200
    assert result.outputs["is_json"] is True
    assert result.outputs["body"]["success"] is True
    assert result.outputs["body"]["data"]["id"] == 123
    
    # Verify the HTTP request was made correctly
    mock_client.get.assert_called_once_with(
        "https://api.example.com/data",
        headers={"Accept": "application/json"},
        params={"query": "test"}
    )
    
    # Check metrics
    assert result.metrics["status_code"] == 200
    assert result.metrics["response_time_ms"] == 500  # 0.5 seconds in ms
    assert result.metrics["content_length"] == len(mock_response.content)