"""
Pytest fixtures for pipeline tests.

This module provides shared fixtures for testing pipeline functionality.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from db.pipeline_models import (
    Pipeline, PipelineStep, PipelineExecution, PipelineStepExecution,
    PipelineExecutionStatus, PipelineStepExecutionStatus, PipelineStepType
)
from pipeline.engine import PipelineEngine, StepExecutionResult


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
def basic_pipeline():
    """Creates a basic mock pipeline."""
    pipeline = MagicMock(spec=Pipeline)
    pipeline.id = "test-pipeline"
    pipeline.name = "Test Pipeline"
    pipeline.user_id = "test-user"
    pipeline.is_public = False
    return pipeline


@pytest.fixture
def basic_steps():
    """Creates a list of basic mock pipeline steps."""
    steps = []
    
    # Step 1: Prompt step
    prompt_step = MagicMock(spec=PipelineStep)
    prompt_step.id = "step1"
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
    
    return steps


@pytest.fixture
def mock_pipeline_execution():
    """Creates a mock pipeline execution."""
    execution = MagicMock(spec=PipelineExecution)
    execution.id = f"exec-{uuid.uuid4()}"
    execution.pipeline_id = "test-pipeline"
    execution.user_id = "test-user"
    execution.status = PipelineExecutionStatus.PENDING.value
    execution.started_at = datetime.now()
    execution.input_parameters = {"topic": "testing"}
    return execution


@pytest.fixture
def mock_step_execution():
    """Creates a mock pipeline step execution."""
    step_execution = MagicMock(spec=PipelineStepExecution)
    step_execution.id = f"step-exec-{uuid.uuid4()}"
    step_execution.pipeline_execution_id = f"exec-{uuid.uuid4()}"
    step_execution.step_id = "step1"
    step_execution.status = PipelineStepExecutionStatus.PENDING.value
    step_execution.started_at = datetime.now()
    step_execution.inputs = {"prompt": "testing"}
    return step_execution


@pytest.fixture
def complex_pipeline():
    """Creates a complex mock pipeline with multiple step types."""
    pipeline = MagicMock(spec=Pipeline)
    pipeline.id = "complex-pipeline"
    pipeline.name = "Complex Pipeline"
    pipeline.user_id = "test-user"
    pipeline.is_public = False
    
    # Create steps with different types
    steps = []
    
    # Step 1: Prompt step
    prompt_step = MagicMock(spec=PipelineStep)
    prompt_step.id = "step1"
    prompt_step.name = "Generate Query"
    prompt_step.type = PipelineStepType.PROMPT.value
    prompt_step.order = 1
    prompt_step.config = {
        "model_id": "test-model",
        "prompt": "Generate a search query for {{input.topic}}"
    }
    prompt_step.input_mapping = {
        "prompt": "input.topic"
    }
    steps.append(prompt_step)
    
    # Step 2: API step
    api_step = MagicMock(spec=PipelineStep)
    api_step.id = "step2"
    api_step.name = "Search API"
    api_step.type = PipelineStepType.API.value
    api_step.order = 2
    api_step.config = {
        "method": "GET",
        "url": "https://api.example.com/search"
    }
    api_step.input_mapping = {
        "params": {
            "q": "output.response",
            "limit": "input.limit"
        }
    }
    steps.append(api_step)
    
    # Step 3: Code step
    code_step = MagicMock(spec=PipelineStep)
    code_step.id = "step3"
    code_step.name = "Process Results"
    code_step.type = PipelineStepType.CODE.value
    code_step.order = 3
    code_step.config = {
        "language": "python",
        "code": "import json\nresults = input_data\nprocessed = [item for item in results if 'score' in item and item['score'] > 0.5]\nprint(json.dumps(processed))"
    }
    code_step.input_mapping = {
        "input_data": "output.body.results"
    }
    steps.append(code_step)
    
    # Step 4: File step
    file_step = MagicMock(spec=PipelineStep)
    file_step.id = "step4"
    file_step.name = "Save Results"
    file_step.type = PipelineStepType.FILE.value
    file_step.order = 4
    file_step.config = {
        "operation": "write",
        "file_path": "/uploads/results.json"
    }
    file_step.input_mapping = {
        "content": "output.result"
    }
    steps.append(file_step)
    
    # Step 5: Final prompt step
    summary_step = MagicMock(spec=PipelineStep)
    summary_step.id = "step5"
    summary_step.name = "Generate Summary"
    summary_step.type = PipelineStepType.PROMPT.value
    summary_step.order = 5
    summary_step.config = {
        "model_id": "test-model",
        "prompt": "Summarize these results: {{output.result}}"
    }
    steps.append(summary_step)
    
    return pipeline, steps