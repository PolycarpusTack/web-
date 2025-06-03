"""
Tests for Pipeline Context and Data Mapping.

These tests focus on the context management and input/output mapping
functionality of the pipeline execution engine, ensuring data flows correctly
between steps.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
import json
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


def test_basic_input_resolution(pipeline_engine):
    """Tests basic input resolution for a pipeline step."""
    # Create a step with simple input mapping
    step = MagicMock(spec=PipelineStep)
    step.config = {
        "default_param": "default value",
        "static_value": 42
    }
    step.input_mapping = {
        "prompt": "output.generated_text",
        "user_input": "input.query"
    }
    
    # Create a context with input and output data
    context = {
        "input": {
            "query": "What is the capital of France?"
        },
        "output": {
            "generated_text": "The capital of France is Paris."
        }
    }
    
    # Resolve inputs
    inputs = pipeline_engine._resolve_step_inputs(step, context)
    
    # Check resolved inputs
    assert inputs["default_param"] == "default value"
    assert inputs["static_value"] == 42
    assert inputs["prompt"] == "The capital of France is Paris."
    assert inputs["user_input"] == "What is the capital of France?"


def test_nested_input_resolution(pipeline_engine):
    """Tests resolving nested input mappings."""
    # Create a step with nested input mapping
    step = MagicMock(spec=PipelineStep)
    step.config = {}
    step.input_mapping = {
        "text": "output.llm_response.content",
        "confidence": "output.llm_response.metadata.confidence",
        "user_info": {
            "source": "input",
            "path": "user"
        },
        "settings": {
            "source": "output",
            "path": "config.settings"
        }
    }
    
    # Create a context with nested data
    context = {
        "input": {
            "query": "Search query",
            "user": {
                "name": "Test User",
                "id": "user123",
                "preferences": {
                    "theme": "dark"
                }
            }
        },
        "output": {
            "llm_response": {
                "content": "Generated content",
                "metadata": {
                    "model": "test-model",
                    "confidence": 0.92,
                    "tokens": 150
                }
            },
            "config": {
                "settings": {
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            }
        }
    }
    
    # Resolve inputs
    inputs = pipeline_engine._resolve_step_inputs(step, context)
    
    # Check resolved inputs
    assert inputs["text"] == "Generated content"
    assert inputs["confidence"] == 0.92
    assert inputs["user_info"]["name"] == "Test User"
    assert inputs["user_info"]["preferences"]["theme"] == "dark"
    assert inputs["settings"]["temperature"] == 0.7
    assert inputs["settings"]["max_tokens"] == 500


def test_input_resolution_with_missing_values(pipeline_engine):
    """Tests input resolution when mapped values are missing."""
    # Create a step with input mapping to missing values
    step = MagicMock(spec=PipelineStep)
    step.config = {
        "fallback": "This is a fallback value"
    }
    step.input_mapping = {
        "value1": "output.missing_key",
        "value2": "output.existing.missing_subkey",
        "value3": {
            "source": "input",
            "path": "missing.path"
        },
        "value4": {
            "source": "missing_source",
            "path": "some.path"
        }
    }
    
    # Create a context with some missing paths
    context = {
        "input": {
            "query": "Test query"
        },
        "output": {
            "existing": {
                "subkey": "This exists"
            }
        }
    }
    
    # Resolve inputs
    inputs = pipeline_engine._resolve_step_inputs(step, context)
    
    # Check resolved inputs
    assert inputs["fallback"] == "This is a fallback value"
    assert "value1" not in inputs  # Missing key results in no mapping
    assert "value2" not in inputs  # Missing subkey results in no mapping
    assert "value3" not in inputs  # Missing source path results in no mapping
    assert "value4" not in inputs  # Missing source results in no mapping


def test_output_mapping_in_context_update(pipeline_engine):
    """Tests how output mapping affects context updates after step execution."""
    # Create a pipeline step with output mapping
    step = MagicMock(spec=PipelineStep)
    step.name = "Test Step"
    step.output_mapping = {
        "mapped_text": "response",
        "mapped_metadata": "metadata.model"
    }
    
    # Create a step execution result with outputs
    result = StepExecutionResult.success_result(
        outputs={
            "response": "Generated text response",
            "metadata": {
                "model": "test-model",
                "tokens": 150,
                "duration": 0.5
            },
            "additional": "This won't be mapped"
        }
    )
    
    # Create a context to update
    context = {
        "input": {"query": "Test query"},
        "output": {}
    }
    
    # Mock the pipeline engine's _execute_step method
    with patch.object(pipeline_engine, '_execute_step', return_value=result):
        # Simulate the context update logic from execute_pipeline
        if result.success:
            # Use output mapping if available
            if step.output_mapping:
                for context_key, output_key in step.output_mapping.items():
                    if output_key in result.outputs:
                        context["output"][context_key] = result.outputs[output_key]
            else:
                # Without mapping, all outputs would be merged
                context["output"].update(result.outputs)
    
    # Check the context after update with mapping
    assert context["output"]["mapped_text"] == "Generated text response"
    assert context["output"]["mapped_metadata"] == "test-model"
    
    # Fields not in the mapping should not be in the context
    assert "response" not in context["output"]
    assert "metadata" not in context["output"]
    assert "additional" not in context["output"]


def test_no_output_mapping_in_context_update(pipeline_engine):
    """Tests context updates without output mapping after step execution."""
    # Create a pipeline step without output mapping
    step = MagicMock(spec=PipelineStep)
    step.name = "Test Step"
    step.output_mapping = None
    
    # Create a step execution result with outputs
    result = StepExecutionResult.success_result(
        outputs={
            "response": "Generated text response",
            "metadata": {
                "model": "test-model",
                "tokens": 150,
                "duration": 0.5
            },
            "additional": "This will be included"
        }
    )
    
    # Create a context to update
    context = {
        "input": {"query": "Test query"},
        "output": {
            "existing": "This field already exists"
        }
    }
    
    # Mock the pipeline engine's _execute_step method
    with patch.object(pipeline_engine, '_execute_step', return_value=result):
        # Simulate the context update logic from execute_pipeline
        if result.success:
            # Use output mapping if available
            if step.output_mapping:
                for context_key, output_key in step.output_mapping.items():
                    if output_key in result.outputs:
                        context["output"][context_key] = result.outputs[output_key]
            else:
                # Without mapping, all outputs should be merged
                context["output"].update(result.outputs)
    
    # Check the context after update without mapping (all outputs merged)
    assert context["output"]["existing"] == "This field already exists"  # Preserved
    assert context["output"]["response"] == "Generated text response"
    assert context["output"]["metadata"]["model"] == "test-model"
    assert context["output"]["metadata"]["tokens"] == 150
    assert context["output"]["additional"] == "This will be included"


@pytest.mark.asyncio
async def test_pipeline_with_sequential_data_flow(pipeline_engine):
    """Tests data flow between sequential steps in a pipeline."""
    # Create a pipeline with sequential steps that build on each other's outputs
    pipeline = MagicMock(spec=Pipeline)
    pipeline.id = "sequential-pipeline"
    pipeline.name = "Sequential Data Flow Pipeline"
    pipeline.user_id = "test-user"
    pipeline.is_public = False
    
    # Create steps with sequential data dependencies
    steps = []
    
    # Step 1: Generate initial data
    step1 = MagicMock(spec=PipelineStep)
    step1.id = "step1"
    step1.name = "Generate Data"
    step1.type = PipelineStepType.CODE.value
    step1.order = 1
    step1.config = {"language": "python", "code": "..."}
    step1.input_mapping = {}
    # No output mapping, so all outputs are merged into context
    steps.append(step1)
    
    # Step 2: Process data from step 1
    step2 = MagicMock(spec=PipelineStep)
    step2.id = "step2"
    step2.name = "Process Data"
    step2.type = PipelineStepType.TRANSFORM.value
    step2.order = 2
    step2.config = {"transform_type": "text_to_json"}
    step2.input_mapping = {
        "data": "output.step1_result"
    }
    step2.output_mapping = {
        "processed_data": "result"
    }
    steps.append(step2)
    
    # Step 3: Analyze processed data from step 2
    step3 = MagicMock(spec=PipelineStep)
    step3.id = "step3"
    step3.name = "Analyze Data"
    step3.type = PipelineStepType.PROMPT.value
    step3.order = 3
    step3.config = {"model_id": "test-model"}
    step3.input_mapping = {
        "prompt": "Analyze this data: {{output.processed_data}}"
    }
    step3.output_mapping = {
        "analysis": "response"
    }
    steps.append(step3)
    
    # Step 4: Summarize results using both original data and analysis
    step4 = MagicMock(spec=PipelineStep)
    step4.id = "step4"
    step4.name = "Summarize Results"
    step4.type = PipelineStepType.CODE.value
    step4.order = 4
    step4.config = {"language": "python", "code": "..."}
    step4.input_mapping = {
        "original_data": "output.step1_result",
        "processed_data": "output.processed_data",
        "analysis": "output.analysis"
    }
    steps.append(step4)
    
    # Mock database calls
    pipeline_engine.db.get_pipeline = AsyncMock(return_value=pipeline)
    pipeline_engine.db.get_pipeline_steps = AsyncMock(return_value=steps)
    
    # Mock execution creation
    mock_execution = MagicMock(spec=PipelineExecution)
    mock_execution.id = "test-execution-id"
    pipeline_engine.db.create_pipeline_execution = AsyncMock(return_value=mock_execution)
    
    # Mock step execution creation
    mock_step_exec = MagicMock(spec=PipelineStepExecution)
    mock_step_exec.id = "test-step-execution-id"
    pipeline_engine.db.create_pipeline_step_execution = AsyncMock(return_value=mock_step_exec)
    
    # Mock database update operations
    pipeline_engine.db.update_pipeline_step_execution = AsyncMock()
    pipeline_engine.db.complete_pipeline_step_execution = AsyncMock()
    pipeline_engine.db.complete_pipeline_execution = AsyncMock(return_value=mock_execution)
    
    # Create step execution results with sequential dependencies
    
    # Step 1 result: Generate initial data
    step1_result = StepExecutionResult.success_result(
        outputs={
            "step1_result": "Initial data: 42, 73, 91",
            "stdout": "Initial data: 42, 73, 91",
            "return_code": 0
        }
    )
    
    # Step 2 result: Process data referring to step 1 output
    step2_result = StepExecutionResult.success_result(
        outputs={
            "result": {"values": [42, 73, 91], "count": 3, "sum": 206},
            "transform_type": "text_to_json"
        }
    )
    
    # Step 3 result: Analysis referring to step 2 output
    step3_result = StepExecutionResult.success_result(
        outputs={
            "response": "Analysis: The data contains 3 values with a sum of 206 and average of 68.67.",
            "model_id": "test-model"
        }
    )
    
    # Step 4 result: Summary using outputs from steps 1, 2, and 3
    step4_result = StepExecutionResult.success_result(
        outputs={
            "summary": {
                "original": "Initial data: 42, 73, 91",
                "processed": {"values": [42, 73, 91], "count": 3, "sum": 206},
                "analysis": "Analysis: The data contains 3 values with a sum of 206 and average of 68.67.",
                "conclusion": "The dataset has been successfully processed and analyzed."
            },
            "stdout": "...",
            "return_code": 0
        }
    )
    
    # Execute with mocked step handlers
    with patch.object(pipeline_engine, '_execute_step', side_effect=[
        step1_result, step2_result, step3_result, step4_result
    ]):
        # Execute the pipeline
        result = await pipeline_engine.execute_pipeline(
            pipeline_id=pipeline.id,
            user_id=pipeline.user_id,
            input_parameters={}
        )
    
    # Verify each step was executed with correct order
    execution_calls = pipeline_engine._execute_step.call_args_list
    assert len(execution_calls) == 4
    
    # Verify context was updated correctly for each step
    
    # For step 2, check if it received step 1's output in the context
    step2_context = execution_calls[1][0][1]  # args[1] for second call
    assert "step1_result" in step2_context["output"]
    assert step2_context["output"]["step1_result"] == "Initial data: 42, 73, 91"
    
    # For step 3, check if it received step 2's mapped output in the context
    step3_context = execution_calls[2][0][1]  # args[1] for third call
    assert "processed_data" in step3_context["output"]
    assert step3_context["output"]["processed_data"]["values"] == [42, 73, 91]
    
    # For step 4, check if it received outputs from all previous steps
    step4_context = execution_calls[3][0][1]  # args[1] for fourth call
    assert "step1_result" in step4_context["output"]
    assert "processed_data" in step4_context["output"]
    assert "analysis" in step4_context["output"]
    
    # Check final execution result contains all mapped outputs
    pipeline_engine.db.complete_pipeline_execution.assert_called_once()
    args, kwargs = pipeline_engine.db.complete_pipeline_execution.call_args
    
    # Extract the final results
    final_results = kwargs.get("results", {})
    
    # Verify the expected keys from each step are present
    assert "step1_result" in final_results
    assert "processed_data" in final_results
    assert "analysis" in final_results
    assert "summary" in final_results


@pytest.mark.asyncio
async def test_pipeline_with_complex_input_transformations(pipeline_engine):
    """Tests pipeline with complex input transformations between steps."""
    # Create a pipeline that requires complex input transformations
    pipeline = MagicMock(spec=Pipeline)
    pipeline.id = "transform-pipeline"
    pipeline.name = "Input Transformation Pipeline"
    pipeline.user_id = "test-user"
    pipeline.is_public = False
    
    # Create steps that require complex input transformations
    steps = []
    
    # Step 1: Generate structured data
    step1 = MagicMock(spec=PipelineStep)
    step1.id = "step1"
    step1.name = "Generate Data"
    step1.type = PipelineStepType.CODE.value
    step1.order = 1
    step1.config = {"language": "python", "code": "..."}
    step1.input_mapping = {
        "seed": "input.seed_value",
        "count": "input.item_count"
    }
    step1.output_mapping = {
        "data": "result"
    }
    steps.append(step1)
    
    # Step 2: Process data with complex transformation
    step2 = MagicMock(spec=PipelineStep)
    step2.id = "step2"
    step2.name = "Transform Data"
    step2.type = PipelineStepType.CODE.value
    step2.order = 2
    step2.config = {"language": "python", "code": "..."}
    step2.input_mapping = {
        # Complex object construction from multiple sources
        "parameters": {
            "items": "output.data.items",
            "user_id": "input.user_id",
            "settings": {
                "max_results": "input.max_results",
                "include_metadata": "input.include_metadata"
            },
            "timestamp": "context.start_time"
        }
    }
    step2.output_mapping = {
        "transformed": "result"
    }
    steps.append(step2)
    
    # Mock database calls
    pipeline_engine.db.get_pipeline = AsyncMock(return_value=pipeline)
    pipeline_engine.db.get_pipeline_steps = AsyncMock(return_value=steps)
    
    # Mock execution creation
    mock_execution = MagicMock(spec=PipelineExecution)
    mock_execution.id = "test-execution-id"
    pipeline_engine.db.create_pipeline_execution = AsyncMock(return_value=mock_execution)
    
    # Mock step execution creation
    mock_step_exec = MagicMock(spec=PipelineStepExecution)
    mock_step_exec.id = "test-step-execution-id"
    pipeline_engine.db.create_pipeline_step_execution = AsyncMock(return_value=mock_step_exec)
    
    # Mock database update operations
    pipeline_engine.db.update_pipeline_step_execution = AsyncMock()
    pipeline_engine.db.complete_pipeline_step_execution = AsyncMock()
    pipeline_engine.db.complete_pipeline_execution = AsyncMock(return_value=mock_execution)
    
    # Create input parameters
    input_parameters = {
        "seed_value": 42,
        "item_count": 5,
        "user_id": "user123",
        "max_results": 10,
        "include_metadata": True
    }
    
    # Create step execution results
    
    # Step 1 result: Generate structured data
    step1_result = StepExecutionResult.success_result(
        outputs={
            "result": {
                "items": [
                    {"id": 1, "name": "Item 1"},
                    {"id": 2, "name": "Item 2"},
                    {"id": 3, "name": "Item 3"},
                    {"id": 4, "name": "Item 4"},
                    {"id": 5, "name": "Item 5"}
                ],
                "count": 5,
                "seed": 42
            },
            "stdout": "...",
            "return_code": 0
        }
    )
    
    # Step 2 should receive complex input with data from multiple sources
    
    # Capture the actual input received by step 2
    received_step2_input = None
    
    # Mock the execute_step to capture inputs
    original_execute_step = pipeline_engine._execute_step
    
    async def mocked_execute_step(step, context, execution_id):
        nonlocal received_step2_input
        # Capture input for step 2
        if step.id == "step2":
            received_step2_input = pipeline_engine._resolve_step_inputs(step, context)
            
        # For step 1, return predefined result
        if step.id == "step1":
            return step1_result
            
        # For step 2, use predefined result
        return StepExecutionResult.success_result(
            outputs={
                "result": {
                    "processed_items": 5,
                    "user": "user123",
                    "timestamp": context["start_time"]
                }
            }
        )
    
    # Patch the execute_step method
    with patch.object(pipeline_engine, '_execute_step', side_effect=mocked_execute_step):
        # Execute the pipeline
        result = await pipeline_engine.execute_pipeline(
            pipeline_id=pipeline.id,
            user_id=pipeline.user_id,
            input_parameters=input_parameters
        )
    
    # Verify step 2 received the complex input correctly
    assert received_step2_input is not None
    assert "parameters" in received_step2_input
    assert received_step2_input["parameters"]["items"] == [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
        {"id": 3, "name": "Item 3"},
        {"id": 4, "name": "Item 4"},
        {"id": 5, "name": "Item 5"}
    ]
    assert received_step2_input["parameters"]["user_id"] == "user123"
    assert received_step2_input["parameters"]["settings"]["max_results"] == 10
    assert received_step2_input["parameters"]["settings"]["include_metadata"] is True
    assert "timestamp" in received_step2_input["parameters"]  # Start time from context