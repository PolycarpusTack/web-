"""
Simple test for pipeline execution core functionality.
This test directly implements a simplified pipeline engine to demonstrate the concept.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
from datetime import datetime
import json
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define enums
class PipelineExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineStepExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class PipelineStepType(str, Enum):
    PROMPT = "prompt"
    TRANSFORM = "transform"
    CODE = "code"
    FILE = "file"
    API = "api"
    CONDITION = "condition"

# Define result class
class StepExecutionResult:
    def __init__(
        self,
        success: bool,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        logs: Optional[List[Dict[str, Any]]] = None
    ):
        self.success = success
        self.outputs = outputs or {}
        self.error = error
        self.metrics = metrics or {}
        self.logs = logs or []
    
    @classmethod
    def success_result(cls, outputs: Dict[str, Any], metrics: Optional[Dict[str, Any]] = None) -> 'StepExecutionResult':
        return cls(success=True, outputs=outputs, metrics=metrics)
    
    @classmethod
    def error_result(cls, error: str, outputs: Optional[Dict[str, Any]] = None) -> 'StepExecutionResult':
        return cls(success=False, error=error, outputs=outputs)

# Define pipeline exception
class PipelineExecutionError(Exception):
    def __init__(self, message: str, step_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.step_id = step_id
        self.details = details or {}
        super().__init__(message)

# Define type for pipeline context
PipelineContext = Dict[str, Any]

# Define mock models
class Pipeline:
    def __init__(self, id: str, name: str, user_id: str, is_public: bool = False):
        self.id = id
        self.name = name
        self.user_id = user_id
        self.is_public = is_public

class PipelineStep:
    def __init__(
        self, 
        id: str, 
        name: str, 
        type: str, 
        order: int,
        config: Dict[str, Any],
        input_mapping: Optional[Dict[str, Any]] = None,
        output_mapping: Optional[Dict[str, Any]] = None,
        pipeline_id: str = "test-pipeline"
    ):
        self.id = id
        self.name = name
        self.type = type
        self.order = order
        self.config = config
        self.input_mapping = input_mapping
        self.output_mapping = output_mapping
        self.pipeline_id = pipeline_id

class PipelineExecution:
    def __init__(
        self,
        id: str,
        pipeline_id: str,
        user_id: str,
        status: str,
        input_parameters: Optional[Dict[str, Any]] = None,
        results: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None
    ):
        self.id = id
        self.pipeline_id = pipeline_id
        self.user_id = user_id
        self.status = status
        self.started_at = datetime.now()
        self.completed_at = None
        self.input_parameters = input_parameters or {}
        self.results = results
        self.error = error

class PipelineStepExecution:
    def __init__(
        self,
        id: str,
        pipeline_execution_id: str,
        step_id: str,
        status: str,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        model_id: Optional[str] = None
    ):
        self.id = id
        self.pipeline_execution_id = pipeline_execution_id
        self.step_id = step_id
        self.status = status
        self.started_at = datetime.now()
        self.completed_at = None
        self.inputs = inputs or {}
        self.outputs = outputs
        self.error = error
        self.model_id = model_id

# Simplified Pipeline Engine
class SimplePipelineEngine:
    def __init__(self):
        logger.info("Initializing SimplePipelineEngine")
        self._step_handlers = {}
        self._current_step = None
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default step handlers."""
        self._step_handlers = {
            PipelineStepType.PROMPT.value: self._execute_prompt_step,
            PipelineStepType.TRANSFORM.value: self._execute_transform_step,
        }
    
    async def execute_pipeline(
        self,
        pipeline_id: str,
        user_id: str,
        input_parameters: Optional[Dict[str, Any]] = None
    ) -> PipelineExecution:
        """Execute a pipeline."""
        logger.info(f"Starting execution of pipeline {pipeline_id} for user {user_id}")
        
        # Create a mock pipeline
        pipeline = Pipeline(
            id=pipeline_id,
            name="Test Pipeline",
            user_id="test-user",
            is_public=True
        )
        
        # Create mock steps
        steps = [
            PipelineStep(
                id="step1",
                name="Generate Content",
                type=PipelineStepType.PROMPT.value,
                order=1,
                config={
                    "model_id": "test-model",
                    "prompt": "Generate content about testing"
                },
                input_mapping={
                    "prompt": "input.topic"
                },
                output_mapping={
                    "generated_text": "response"
                }
            ),
            PipelineStep(
                id="step2",
                name="Process Content",
                type=PipelineStepType.TRANSFORM.value,
                order=2,
                config={
                    "transform_type": "text_to_json"
                },
                input_mapping={
                    "data": "output.generated_text",
                    "transform_type": "config.transform_type"
                },
                output_mapping=None
            )
        ]
        
        # Check access permission
        if pipeline.user_id != user_id and not pipeline.is_public:
            raise PipelineExecutionError("Not authorized to execute this pipeline")
        
        # Create execution record
        execution_id = str(uuid.uuid4())
        execution = PipelineExecution(
            id=execution_id,
            pipeline_id=pipeline_id,
            user_id=user_id,
            status=PipelineExecutionStatus.PENDING.value,
            input_parameters=input_parameters or {}
        )
        
        # Initialize pipeline context
        context: PipelineContext = {
            "input": input_parameters or {},
            "output": {},
            "execution_id": execution.id,
            "pipeline_id": pipeline_id,
            "user_id": user_id,
            "start_time": datetime.now().isoformat()
        }
        
        # Update execution status to running
        execution.status = PipelineExecutionStatus.RUNNING.value
        logger.info(f"Pipeline execution {execution.id} status updated to RUNNING")
        
        # Execute steps
        try:
            # Sort steps by order
            steps.sort(key=lambda s: s.order)
            
            # Process each step
            for step in steps:
                step_result = await self._execute_step(step, context, execution.id)
                
                # Update context with step outputs
                if step_result.success:
                    # Use output mapping if available, otherwise use all outputs
                    if step.output_mapping:
                        for context_key, output_key in step.output_mapping.items():
                            if output_key in step_result.outputs:
                                context["output"][context_key] = step_result.outputs[output_key]
                    else:
                        # Merge outputs into context
                        context["output"].update(step_result.outputs)
                else:
                    # Step failed, stop pipeline execution
                    raise PipelineExecutionError(
                        f"Step execution failed: {step.name}", 
                        step_id=step.id,
                        details={"error": step_result.error}
                    )
            
            # All steps completed successfully
            context["end_time"] = datetime.now().isoformat()
            
            # Mark execution as completed
            execution.status = PipelineExecutionStatus.COMPLETED.value
            execution.completed_at = datetime.now()
            execution.results = context["output"]
            logger.info(f"Pipeline execution {execution.id} completed successfully")
            
            return execution
            
        except PipelineExecutionError as e:
            # Log the error
            logger.error(f"Pipeline execution error: {str(e)}")
            
            # Mark execution as failed
            execution.status = PipelineExecutionStatus.FAILED.value
            execution.completed_at = datetime.now()
            execution.error = str(e)
            execution.results = context.get("output")
            logger.info(f"Pipeline execution {execution.id} failed: {str(e)}")
            
            return execution
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error during pipeline execution: {str(e)}"
            logger.exception(error_msg)
            
            # Mark execution as failed
            execution.status = PipelineExecutionStatus.FAILED.value
            execution.completed_at = datetime.now()
            execution.error = error_msg
            execution.results = context.get("output")
            logger.info(f"Pipeline execution {execution.id} failed with unexpected error: {str(e)}")
            
            return execution
    
    async def _execute_step(
        self,
        step: PipelineStep,
        context: PipelineContext,
        execution_id: str
    ) -> StepExecutionResult:
        """Execute a single pipeline step."""
        logger.info(f"Executing step: {step.name} (type: {step.type})")
        
        # Set current step for reference in other methods
        self._current_step = step
        
        # Resolve step inputs
        step_inputs = self._resolve_step_inputs(step, context)
        logger.info(f"Resolved inputs: {json.dumps(step_inputs, default=str)}")
        
        # Create step execution record
        step_execution_id = str(uuid.uuid4())
        step_execution = PipelineStepExecution(
            id=step_execution_id,
            pipeline_execution_id=execution_id,
            step_id=step.id,
            status=PipelineStepExecutionStatus.PENDING.value,
            inputs=step_inputs
        )
        logger.info(f"Created step execution {step_execution.id}")
        
        # Update status to running
        step_execution.status = PipelineStepExecutionStatus.RUNNING.value
        logger.info(f"Step execution {step_execution.id} status updated to RUNNING")
        
        start_time = datetime.now()
        
        try:
            # Get the appropriate handler for this step type
            handler = self._step_handlers.get(step.type)
            if not handler:
                raise PipelineExecutionError(f"No handler found for step type: {step.type}")
            
            # Execute the step
            # Add execution context to step inputs
            execution_context = {
                "step_execution_id": step_execution.id,
                "pipeline_execution_id": execution_id,
                "pipeline_id": context["pipeline_id"],
                "user_id": context["user_id"]
            }
            
            logger.info(f"Calling handler for step type: {step.type}")
            result = await handler(step, step_inputs, execution_context)
            logger.info(f"Handler result success: {result.success}")
            
            # Calculate metrics
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            if not result.metrics:
                result.metrics = {}
            result.metrics["duration_ms"] = duration_ms
            
            # Update step execution record
            if result.success:
                step_execution.status = PipelineStepExecutionStatus.COMPLETED.value
                step_execution.completed_at = datetime.now()
                step_execution.outputs = result.outputs
                logger.info(f"Step execution {step_execution.id} completed successfully")
            else:
                step_execution.status = PipelineStepExecutionStatus.FAILED.value
                step_execution.completed_at = datetime.now()
                step_execution.outputs = result.outputs
                step_execution.error = result.error
                logger.info(f"Step execution {step_execution.id} failed: {result.error}")
            
            return result
            
        except Exception as e:
            # Log the error
            error_msg = f"Error executing step {step.name}: {str(e)}"
            logger.exception(error_msg)
            
            # Calculate metrics
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            
            # Update step execution record
            step_execution.status = PipelineStepExecutionStatus.FAILED.value
            step_execution.completed_at = datetime.now()
            step_execution.error = error_msg
            logger.info(f"Step execution {step_execution.id} failed with exception: {str(e)}")
            
            # Return error result
            return StepExecutionResult.error_result(error_msg)
    
    def _resolve_step_inputs(self, step: PipelineStep, context: PipelineContext) -> Dict[str, Any]:
        """Resolve inputs for a step based on its input mapping and the context."""
        resolved_inputs = {}
        
        # First copy the step's config (default values)
        if step.config:
            resolved_inputs.update(step.config)
        
        # Apply input mapping if available
        if step.input_mapping:
            for input_key, mapping in step.input_mapping.items():
                value = self._get_value_from_context(mapping, context)
                if value is not None:
                    resolved_inputs[input_key] = value
        
        return resolved_inputs
    
    def _get_value_from_context(self, mapping: Any, context: PipelineContext) -> Any:
        """Get a value from the context based on a mapping."""
        source = "output"
        path = None
        
        if isinstance(mapping, str):
            path = mapping
        elif isinstance(mapping, dict):
            source = mapping.get("source", "output")
            path = mapping.get("path")
        
        if not path:
            return None
        
        # Special case for config references
        if source == "config" and hasattr(self, "_current_step") and self._current_step:
            source_data = self._current_step.config
        else:
            # Get the source data from context
            source_data = context.get(source, {})
        
        # Simple path lookup
        if "." not in path:
            return source_data.get(path)
        
        # Nested path lookup
        parts = path.split(".")
        value = source_data
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    return None
            else:
                return None
        
        return value
    
    # Step handlers
    
    async def _execute_prompt_step(
        self,
        step: PipelineStep,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> StepExecutionResult:
        """Execute a prompt step, which sends a prompt to an LLM."""
        try:
            # Extract required parameters
            model_id = inputs.get("model_id")
            if not model_id:
                return StepExecutionResult.error_result("No model_id provided for prompt step")
            
            prompt = inputs.get("prompt")
            if not prompt:
                return StepExecutionResult.error_result("No prompt provided for prompt step")
            
            logger.info(f"Executing prompt step with model {model_id}: {prompt}")
            
            # For this test, we'll mock the LLM response
            response = f"This is a simulated response to: {prompt}"
            
            # Create some mock metrics
            metrics = {
                "tokens_prompt": 20,
                "tokens_completion": 30,
                "tokens_total": 50,
                "cost_prompt": 0.0002,
                "cost_completion": 0.0006,
                "cost_total": 0.0008
            }
            
            logger.info(f"Generated response: {response}")
            
            return StepExecutionResult.success_result(
                outputs={
                    "response": response,
                    "model_id": model_id
                },
                metrics=metrics
            )
            
        except Exception as e:
            logger.exception(f"Error in prompt step: {str(e)}")
            return StepExecutionResult.error_result(f"Error in prompt step: {str(e)}")
    
    async def _execute_transform_step(
        self,
        step: PipelineStep,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> StepExecutionResult:
        """Execute a transform step, which transforms data."""
        try:
            # Extract required parameters
            transform_type = inputs.get("transform_type")
            if not transform_type:
                return StepExecutionResult.error_result("No transform_type provided for transform step")
            
            data = inputs.get("data")
            if data is None:
                return StepExecutionResult.error_result("No data provided for transform step")
            
            logger.info(f"Executing transform step with type {transform_type}: {data}")
            
            # Implement a simple transformation
            if transform_type == "text_to_json":
                # Mock a JSON transformation of the text
                result = {
                    "content": data,
                    "type": "json",
                    "length": len(data),
                    "timestamp": datetime.now().isoformat()
                }
            elif transform_type == "json_to_text":
                if isinstance(data, dict):
                    result = json.dumps(data, indent=2)
                else:
                    result = str(data)
            else:
                result = data  # Pass through
            
            logger.info(f"Transformed result: {result}")
            
            return StepExecutionResult.success_result(
                outputs={"result": result, "transform_type": transform_type}
            )
            
        except Exception as e:
            logger.exception(f"Error in transform step: {str(e)}")
            return StepExecutionResult.error_result(f"Error in transform step: {str(e)}")

async def main():
    # Create the engine
    engine = SimplePipelineEngine()
    
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
        
        logger.info("======= Pipeline Execution Result =======")
        logger.info(f"Status: {result.status}")
        logger.info(f"Results: {json.dumps(result.results, indent=2, default=str)}")
        if result.error:
            logger.info(f"Error: {result.error}")
        
    except Exception as e:
        logger.error(f"Error executing pipeline: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())