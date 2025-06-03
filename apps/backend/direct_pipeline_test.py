"""
Direct test for the pipeline execution engine.

This script creates a simplified environment to test the pipeline execution engine
without needing the full database setup.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create mock models for testing
class MockBase:
    pass

class MockModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

class MockPipeline(MockModel):
    pass

class MockPipelineStep(MockModel):
    pass

class MockPipelineExecution(MockModel):
    pass

class MockPipelineStepExecution(MockModel):
    pass

class MockUser(MockModel):
    pass

# Mock database session
class MockAsyncSession:
    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
        
    async def commit(self):
        pass
        
    async def rollback(self):
        pass
        
    async def close(self):
        pass
        
    async def execute(self, query):
        return MockResult()

class MockResult:
    def scalar_one_or_none(self):
        return None
        
    def scalars(self):
        return self
        
    def all(self):
        return []

# Mock pipeline execution engine
from pipeline.engine import PipelineEngine, StepExecutionResult

# Mock CRUD functions
async def mock_get_pipeline(db, pipeline_id):
    """Mock get_pipeline function."""
    return MockPipeline(
        id=pipeline_id,
        name="Test Pipeline",
        user_id="test-user",
        is_public=True
    )

async def mock_get_pipeline_steps(db, pipeline_id, include_disabled=False):
    """Mock get_pipeline_steps function."""
    return [
        MockPipelineStep(
            id="step1",
            name="Generate Content",
            type="prompt",
            order=1,
            config={
                "model_id": "test-model",
                "prompt": "Generate content about {{input.topic}}"
            },
            input_mapping={
                "prompt": "input.topic"
            },
            output_mapping={
                "generated_text": "response"
            }
        ),
        MockPipelineStep(
            id="step2",
            name="Process Content",
            type="transform",
            order=2,
            config={
                "transform_type": "text_to_json"
            },
            input_mapping={
                "data": "output.generated_text"
            },
            output_mapping=None
        )
    ]

async def mock_create_pipeline_execution(db, pipeline_id, user_id, input_parameters=None):
    """Mock create_pipeline_execution function."""
    return MockPipelineExecution(
        id=f"exec-{uuid.uuid4()}",
        pipeline_id=pipeline_id,
        user_id=user_id,
        status="pending",
        started_at=datetime.now(),
        input_parameters=input_parameters or {}
    )

async def mock_complete_pipeline_execution(db, execution_id, status, results=None, error=None):
    """Mock complete_pipeline_execution function."""
    execution = MockPipelineExecution(
        id=execution_id,
        status=status.value if hasattr(status, 'value') else status,
        completed_at=datetime.now(),
        results=results,
        error=error
    )
    logger.info(f"Pipeline execution {execution_id} completed with status: {status}")
    if results:
        logger.info(f"Results: {results}")
    if error:
        logger.info(f"Error: {error}")
    return execution

async def mock_create_pipeline_step_execution(db, execution_id, step_id, inputs=None, model_id=None):
    """Mock create_pipeline_step_execution function."""
    return MockPipelineStepExecution(
        id=f"step-exec-{uuid.uuid4()}",
        pipeline_execution_id=execution_id,
        step_id=step_id,
        status="pending",
        started_at=datetime.now(),
        inputs=inputs or {},
        model_id=model_id
    )

async def mock_update_pipeline_step_execution(db, step_execution_id, data):
    """Mock update_pipeline_step_execution function."""
    logger.info(f"Updating step execution {step_execution_id} with: {data}")
    return None

async def mock_complete_pipeline_step_execution(db, step_execution_id, status, outputs=None, error=None, metrics=None):
    """Mock complete_pipeline_step_execution function."""
    step_exec = MockPipelineStepExecution(
        id=step_execution_id,
        status=status.value if hasattr(status, 'value') else status,
        completed_at=datetime.now(),
        outputs=outputs,
        error=error,
        metrics=metrics
    )
    logger.info(f"Step execution {step_execution_id} completed with status: {status}")
    if outputs:
        logger.info(f"Outputs: {outputs}")
    if error:
        logger.info(f"Error: {error}")
    return step_exec

async def mock_append_step_execution_log(db, step_execution_id, log_entry):
    """Mock append_step_execution_log function."""
    logger.info(f"Appending log to step execution {step_execution_id}: {log_entry}")
    return True

async def mock_get_model(db, model_id):
    """Mock get_model function."""
    return MockModel(
        id=model_id,
        name="Test Model",
        provider="test",
        description="Test model for pipeline",
        version="1.0"
    )

# Mock the step handlers
async def mock_execute_prompt_step(step, inputs, context):
    """Mock prompt step handler."""
    prompt = inputs.get("prompt", "Default prompt")
    logger.info(f"Executing prompt step with: {prompt}")
    
    return StepExecutionResult.success_result(
        outputs={
            "response": f"Generated content about {prompt}",
            "model_id": "test-model"
        },
        metrics={"tokens": 100}
    )

async def mock_execute_transform_step(step, inputs, context):
    """Mock transform step handler."""
    data = inputs.get("data", "Default data")
    logger.info(f"Executing transform step with: {data}")
    
    return StepExecutionResult.success_result(
        outputs={
            "result": {"content": data, "type": "transformed"},
            "transform_type": "text_to_json"
        }
    )

# Patch the functions in the PipelineEngine
def patch_engine(engine):
    # Patch CRUD functions
    import db.pipeline_crud
    db.pipeline_crud.get_pipeline = mock_get_pipeline
    db.pipeline_crud.get_pipeline_steps = mock_get_pipeline_steps
    db.pipeline_crud.create_pipeline_execution = mock_create_pipeline_execution
    db.pipeline_crud.complete_pipeline_execution = mock_complete_pipeline_execution
    db.pipeline_crud.create_pipeline_step_execution = mock_create_pipeline_step_execution
    db.pipeline_crud.update_pipeline_step_execution = mock_update_pipeline_step_execution
    db.pipeline_crud.complete_pipeline_step_execution = mock_complete_pipeline_step_execution
    db.pipeline_crud.append_step_execution_log = mock_append_step_execution_log
    
    # Patch step handlers
    engine._execute_prompt_step = mock_execute_prompt_step
    engine._execute_transform_step = mock_execute_transform_step
    
    # Patch model retrieval
    import db.crud
    db.crud.get_model = mock_get_model
    
    return engine

async def main():
    """Test the pipeline execution engine."""
    # Create a mock session
    db = MockAsyncSession()
    
    # Create and patch the engine
    engine = PipelineEngine(db)
    engine = patch_engine(engine)
    
    # Define test parameters
    pipeline_id = "test-pipeline"
    user_id = "test-user"
    input_parameters = {"topic": "Testing pipelines"}
    
    # Execute the pipeline
    try:
        logger.info(f"Executing pipeline {pipeline_id} with inputs: {input_parameters}")
        result = await engine.execute_pipeline(
            pipeline_id=pipeline_id,
            user_id=user_id,
            input_parameters=input_parameters
        )
        
        logger.info(f"Pipeline execution completed successfully with ID: {result.id}")
        logger.info(f"Status: {result.status}")
        logger.info(f"Results: {result.results}")
        
    except Exception as e:
        logger.error(f"Error executing pipeline: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())