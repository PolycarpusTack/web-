"""
Pipeline Execution Engine for Code Factory.

This module provides the core logic for executing pipeline steps,
managing state between steps, and tracking execution progress.
"""

import asyncio
import logging
import time
import traceback
import sys
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from db.pipeline_models import (
    Pipeline, PipelineStep, PipelineExecution, PipelineStepExecution,
    PipelineExecutionStatus, PipelineStepExecutionStatus, PipelineStepType
)
from db.pipeline_crud import (
    get_pipeline, get_pipeline_steps,
    create_pipeline_execution, complete_pipeline_execution,
    create_pipeline_step_execution, complete_pipeline_step_execution,
    update_pipeline_step_execution, append_step_execution_log
)
from db.crud import get_model

# Configure logging
logger = logging.getLogger(__name__)

# Type for pipeline context
PipelineContext = Dict[str, Any]


class PipelineExecutionError(Exception):
    """Exception raised for errors during pipeline execution."""
    
    def __init__(self, message: str, step_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.step_id = step_id
        self.details = details or {}
        super().__init__(message)


class StepExecutionResult:
    """Result of a pipeline step execution."""
    
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
        """Create a successful result."""
        return cls(success=True, outputs=outputs, metrics=metrics)
    
    @classmethod
    def error_result(cls, error: str, outputs: Optional[Dict[str, Any]] = None) -> 'StepExecutionResult':
        """Create an error result."""
        return cls(success=False, error=error, outputs=outputs)


class PipelineEngine:
    """
    Pipeline execution engine.
    
    This class handles the execution of pipeline steps, manages the pipeline
    context, and tracks execution progress.
    """
    
    def __init__(self, db: AsyncSession):
        """Initialize the pipeline engine."""
        self.db = db
        self._step_handlers: Dict[str, Callable] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default step handlers."""
        self._step_handlers = {
            PipelineStepType.PROMPT.value: self._execute_prompt_step,
            PipelineStepType.CODE.value: self._execute_code_step,
            PipelineStepType.FILE.value: self._execute_file_step,
            PipelineStepType.API.value: self._execute_api_step,
            PipelineStepType.CONDITION.value: self._execute_condition_step,
            PipelineStepType.TRANSFORM.value: self._execute_transform_step,
        }
    
    def register_step_handler(self, step_type: str, handler: Callable):
        """
        Register a custom step handler.
        
        Args:
            step_type: The type of step the handler can execute
            handler: Callable that takes step, context, and execution_id and returns StepExecutionResult
        """
        self._step_handlers[step_type] = handler
    
    async def execute_pipeline(
        self,
        pipeline_id: str,
        user_id: str,
        input_parameters: Optional[Dict[str, Any]] = None
    ) -> PipelineExecution:
        """
        Execute a pipeline.
        
        Args:
            pipeline_id: ID of the pipeline to execute
            user_id: ID of the user executing the pipeline
            input_parameters: Optional input parameters for the pipeline
            
        Returns:
            The completed pipeline execution record
            
        Raises:
            PipelineExecutionError: If the pipeline execution fails
        """
        # Get the pipeline
        pipeline = await get_pipeline(self.db, pipeline_id)
        if not pipeline:
            raise PipelineExecutionError(f"Pipeline not found: {pipeline_id}")
        
        # Check authorization
        if pipeline.user_id != user_id and not pipeline.is_public:
            raise PipelineExecutionError("Not authorized to execute this pipeline")
        
        # Get pipeline steps
        steps = await get_pipeline_steps(self.db, pipeline_id, include_disabled=False)
        if not steps:
            raise PipelineExecutionError(f"Pipeline has no enabled steps: {pipeline_id}")
        
        # Create execution record
        execution = await create_pipeline_execution(
            self.db, 
            pipeline_id, 
            user_id, 
            input_parameters or {}
        )
        
        # Initialize pipeline context with input parameters
        context: PipelineContext = {
            "input": input_parameters or {},
            "output": {},
            "execution_id": execution.id,
            "pipeline_id": pipeline_id,
            "user_id": user_id,
            "start_time": datetime.now().isoformat()
        }
        
        # Update execution status to running
        await self._update_execution_status(
            execution.id, 
            PipelineExecutionStatus.RUNNING
        )
        
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
            return await complete_pipeline_execution(
                self.db,
                execution.id,
                PipelineExecutionStatus.COMPLETED,
                results=context["output"]
            )
            
        except PipelineExecutionError as e:
            # Log the error
            logger.error(f"Pipeline execution error: {str(e)}")
            
            # Mark execution as failed
            return await complete_pipeline_execution(
                self.db,
                execution.id,
                PipelineExecutionStatus.FAILED,
                error=str(e),
                results=context.get("output")
            )
        except Exception as e:
            # Unexpected error
            error_msg = f"Unexpected error during pipeline execution: {str(e)}"
            logger.exception(error_msg)
            
            # Mark execution as failed
            return await complete_pipeline_execution(
                self.db,
                execution.id,
                PipelineExecutionStatus.FAILED,
                error=error_msg,
                results=context.get("output")
            )
    
    async def _execute_step(
        self,
        step: PipelineStep,
        context: PipelineContext,
        execution_id: str
    ) -> StepExecutionResult:
        """
        Execute a single pipeline step.
        
        Args:
            step: The pipeline step to execute
            context: The current pipeline context
            execution_id: The ID of the current pipeline execution
            
        Returns:
            StepExecutionResult containing the step's outputs or error
        """
        # Create step execution record
        step_inputs = self._resolve_step_inputs(step, context)
        
        model_id = None
        if step.type == PipelineStepType.PROMPT.value and step.config.get("model_id"):
            model_id = step.config.get("model_id")
        
        step_execution = await create_pipeline_step_execution(
            self.db, 
            execution_id, 
            step.id, 
            inputs=step_inputs,
            model_id=model_id
        )
        
        # Update status to running
        await update_pipeline_step_execution(
            self.db,
            step_execution.id,
            {"status": PipelineStepExecutionStatus.RUNNING.value}
        )
        
        start_time = time.time()
        
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
            
            result = await handler(step, step_inputs, execution_context)
            
            # Calculate metrics
            duration_ms = int((time.time() - start_time) * 1000)
            if not result.metrics:
                result.metrics = {}
            result.metrics["duration_ms"] = duration_ms
            
            # Update step execution record
            if result.success:
                await complete_pipeline_step_execution(
                    self.db,
                    step_execution.id,
                    PipelineStepExecutionStatus.COMPLETED,
                    outputs=result.outputs,
                    metrics=result.metrics
                )
            else:
                await complete_pipeline_step_execution(
                    self.db,
                    step_execution.id,
                    PipelineStepExecutionStatus.FAILED,
                    outputs=result.outputs,
                    error=result.error,
                    metrics=result.metrics
                )
            
            # Add logs if any
            if result.logs:
                for log_entry in result.logs:
                    await append_step_execution_log(self.db, step_execution.id, log_entry)
            
            return result
            
        except Exception as e:
            # Log the error
            error_msg = f"Error executing step {step.name}: {str(e)}"
            logger.exception(error_msg)
            
            # Calculate metrics
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Update step execution record
            await complete_pipeline_step_execution(
                self.db,
                step_execution.id,
                PipelineStepExecutionStatus.FAILED,
                error=error_msg,
                metrics={"duration_ms": duration_ms}
            )
            
            # Return error result
            return StepExecutionResult.error_result(error_msg)
    
    def _resolve_step_inputs(self, step: PipelineStep, context: PipelineContext) -> Dict[str, Any]:
        """
        Resolve inputs for a step based on its input mapping and the context.
        
        Args:
            step: The pipeline step
            context: The current pipeline context
            
        Returns:
            Dict containing the resolved inputs for the step
        """
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
    
    def _get_value_from_context(self, mapping: Union[str, Dict[str, Any]], context: PipelineContext) -> Any:
        """
        Get a value from the context based on a mapping.
        
        Args:
            mapping: Either a string path or a dictionary with source and path
            context: The current pipeline context
            
        Returns:
            The resolved value or None if not found
        """
        source = "output"
        path = None
        
        if isinstance(mapping, str):
            path = mapping
        elif isinstance(mapping, dict):
            source = mapping.get("source", "output")
            path = mapping.get("path")
        
        if not path:
            return None
        
        # Get the source data
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
    
    async def _update_execution_status(
        self,
        execution_id: str,
        status: PipelineExecutionStatus
    ) -> None:
        """Update the status of a pipeline execution."""
        await complete_pipeline_execution(
            self.db,
            execution_id,
            status
        )
    
    # Step handlers
    
    async def _execute_prompt_step(
        self,
        step: PipelineStep,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> StepExecutionResult:
        """
        Execute a prompt step, which sends a prompt to an LLM.
        
        Args:
            step: The pipeline step
            inputs: The resolved inputs for the step
            context: Execution context
            
        Returns:
            StepExecutionResult with LLM response
        """
        try:
            # Extract required parameters
            model_id = inputs.get("model_id")
            if not model_id:
                return StepExecutionResult.error_result("No model_id provided for prompt step")
            
            prompt = inputs.get("prompt")
            if not prompt:
                return StepExecutionResult.error_result("No prompt provided for prompt step")
            
            system_prompt = inputs.get("system_prompt")
            options = inputs.get("options", {})
            stream = inputs.get("stream", False)
            
            # Get model
            model = await get_model(self.db, model_id)
            if not model:
                return StepExecutionResult.error_result(f"Model not found: {model_id}")
            
            # Import main app to access the HTTP client
            import sys
            from pathlib import Path
            # Make sure parent directory is in path
            parent_dir = str(Path(__file__).resolve().parent.parent)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            import main
            
            # Access the HTTP client from the main app
            client = main.app.state.http_client
            
            # Prepare the payload based on model type
            if "chat" in model_id.lower():
                # Ollama chat endpoint format
                payload = {
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt} if system_prompt else None,
                        {"role": "user", "content": prompt}
                    ],
                    "stream": stream
                }
                # Remove None values from messages
                payload["messages"] = [msg for msg in payload["messages"] if msg]
                
                # Add any additional options
                if options:
                    payload["options"] = options
                    
                # Make the API call
                endpoint = "/api/chat"
                
            else:
                # Ollama generation endpoint format
                full_prompt = prompt
                if system_prompt:
                    full_prompt = f"{system_prompt}\n\n{prompt}"
                    
                payload = {
                    "model": model_id,
                    "prompt": full_prompt,
                    "stream": stream
                }
                
                # Add any additional options
                if options:
                    payload["options"] = options
                    
                # Make the API call
                endpoint = "/api/generate"
            
            # Log the API call (sanitizing prompt for logging)
            logger.info(f"Sending prompt to model {model_id}: {prompt[:100]}...")
            
            # Make the request to Ollama
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            response_data = response.json()
            
            # Extract the response based on endpoint type
            content = ""
            if endpoint == "/api/chat":
                content = response_data.get("message", {}).get("content", "")
            else:
                content = response_data.get("response", "")
            
            # Extract metrics
            prompt_tokens = response_data.get("prompt_eval_count", 0)
            completion_tokens = response_data.get("eval_count", 0)
            total_tokens = prompt_tokens + completion_tokens
            
            # Calculate cost based on model rates (simplified)
            prompt_cost = prompt_tokens * 0.00001  # $0.01 per 1000 tokens
            completion_cost = completion_tokens * 0.00002  # $0.02 per 1000 tokens
            total_cost = prompt_cost + completion_cost
            
            # Create metrics
            metrics = {
                "tokens_prompt": prompt_tokens,
                "tokens_completion": completion_tokens,
                "tokens_total": total_tokens,
                "cost_prompt": prompt_cost,
                "cost_completion": completion_cost,
                "cost_total": total_cost
            }
            
            return StepExecutionResult.success_result(
                outputs={
                    "response": content,
                    "raw_response": response_data,
                    "model_id": model_id
                },
                metrics=metrics
            )
            
        except Exception as e:
            logger.exception(f"Error in prompt step: {str(e)}")
            return StepExecutionResult.error_result(f"Error in prompt step: {str(e)}")
    
    async def _execute_code_step(
        self,
        step: PipelineStep,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> StepExecutionResult:
        """
        Execute a code step, which runs a code snippet.
        
        Args:
            step: The pipeline step
            inputs: The resolved inputs for the step
            context: Execution context
            
        Returns:
            StepExecutionResult with code execution results
        """
        try:
            # Extract required parameters
            code = inputs.get("code")
            if not code:
                return StepExecutionResult.error_result("No code provided for code step")
            
            language = inputs.get("language", "python")
            timeout = inputs.get("timeout", 30)  # Default 30s timeout
            parameters = inputs.get("parameters", {})
            
            import asyncio
            import tempfile
            import os
            import subprocess
            import json
            from uuid import uuid4
            
            # Setup execution environment
            if language.lower() == "python":
                # Create a temporary file with the code
                with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as temp_file:
                    temp_path = temp_file.name
                    # Use parameters as environment variables for the execution
                    env_vars = os.environ.copy()
                    
                    # Convert parameters to strings and add as env vars
                    for key, value in parameters.items():
                        if isinstance(value, (dict, list)):
                            env_vars[key] = json.dumps(value)
                        else:
                            env_vars[key] = str(value)
                    
                    # Write the code to the file
                    temp_file.write(code.encode('utf-8'))
                
                try:
                    # Create a subprocess to run the code with timeout
                    process = await asyncio.create_subprocess_exec(
                        sys.executable, temp_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env=env_vars
                    )
                    
                    # Wait for the process to complete with timeout
                    try:
                        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
                        stdout = stdout.decode('utf-8')
                        stderr = stderr.decode('utf-8')
                        return_code = process.returncode
                        
                        # Build result
                        result = {
                            "stdout": stdout,
                            "stderr": stderr,
                            "return_code": return_code,
                            "success": return_code == 0
                        }
                        
                        # Try to parse stdout as JSON if it looks like JSON
                        if stdout.strip().startswith('{') and stdout.strip().endswith('}'):
                            try:
                                parsed_output = json.loads(stdout)
                                result["parsed_output"] = parsed_output
                            except json.JSONDecodeError:
                                pass
                        
                        # If successful, include parsed output in main output if available
                        if return_code == 0:
                            if "parsed_output" in result:
                                result["result"] = result["parsed_output"]
                            else:
                                result["result"] = stdout.strip()
                        
                        # Add logs for execution details
                        logs = [
                            {"level": "info", "message": f"Executed Python code with return code {return_code}"}
                        ]
                        
                        if stderr and return_code != 0:
                            logs.append({"level": "error", "message": stderr})
                        
                        return StepExecutionResult(
                            success=return_code == 0,
                            outputs=result,
                            error=stderr if return_code != 0 else None,
                            logs=logs
                        )
                        
                    except asyncio.TimeoutError:
                        # Kill the process if it times out
                        process.kill()
                        error_msg = f"Code execution timed out after {timeout} seconds"
                        logger.error(error_msg)
                        return StepExecutionResult.error_result(error_msg)
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete temporary file {temp_path}: {str(e)}")
            
            elif language.lower() == "javascript" or language.lower() == "node":
                # Implementation for Node.js execution (similar to Python)
                with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as temp_file:
                    temp_path = temp_file.name
                    # Write the code to the file
                    temp_file.write(code.encode('utf-8'))
                
                try:
                    # Create a subprocess to run the code with timeout
                    process = await asyncio.create_subprocess_exec(
                        "node", temp_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE,
                        env=os.environ.copy()
                    )
                    
                    # Wait for the process to complete with timeout
                    try:
                        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout)
                        stdout = stdout.decode('utf-8')
                        stderr = stderr.decode('utf-8')
                        return_code = process.returncode
                        
                        result = {
                            "stdout": stdout,
                            "stderr": stderr,
                            "return_code": return_code,
                            "success": return_code == 0
                        }
                        
                        # Try to parse stdout as JSON
                        if stdout.strip().startswith('{') and stdout.strip().endswith('}'):
                            try:
                                parsed_output = json.loads(stdout)
                                result["parsed_output"] = parsed_output
                                result["result"] = parsed_output
                            except json.JSONDecodeError:
                                result["result"] = stdout.strip()
                        else:
                            result["result"] = stdout.strip()
                        
                        return StepExecutionResult(
                            success=return_code == 0,
                            outputs=result,
                            error=stderr if return_code != 0 else None
                        )
                        
                    except asyncio.TimeoutError:
                        process.kill()
                        error_msg = f"Code execution timed out after {timeout} seconds"
                        logger.error(error_msg)
                        return StepExecutionResult.error_result(error_msg)
                    
                finally:
                    # Clean up temporary file
                    try:
                        os.unlink(temp_path)
                    except Exception as e:
                        logger.warning(f"Failed to delete temporary file {temp_path}: {str(e)}")
            
            else:
                # Unsupported language
                return StepExecutionResult.error_result(
                    f"Unsupported language: {language}. Supported languages: python, javascript"
                )
            
        except Exception as e:
            logger.exception(f"Error in code step: {str(e)}")
            return StepExecutionResult.error_result(f"Error in code step: {str(e)}")
    
    async def _execute_file_step(
        self,
        step: PipelineStep,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> StepExecutionResult:
        """
        Execute a file step, which reads or writes a file.
        
        Args:
            step: The pipeline step
            inputs: The resolved inputs for the step
            context: Execution context
            
        Returns:
            StepExecutionResult with file operation results
        """
        try:
            # Extract required parameters
            operation = inputs.get("operation")
            if not operation:
                return StepExecutionResult.error_result("No operation provided for file step")
            
            file_path = inputs.get("file_path")
            if not file_path:
                return StepExecutionResult.error_result("No file_path provided for file step")
            
            # Import file-related modules
            import os
            import aiofiles
            import json
            from pathlib import Path
            
            # Validate file path for security
            normalized_path = os.path.normpath(file_path)
            
            # Restrict file access to an uploads directory for security
            # Get the uploads dir from main app settings
            import main
            uploads_dir = main.settings.upload_dir
            
            # Ensure the path is within the allowed area
            absolute_path = os.path.abspath(normalized_path)
            uploads_absolute = os.path.abspath(uploads_dir)
            
            # Only allow operations in the uploads directory
            if not absolute_path.startswith(uploads_absolute):
                # For safety, restrict file operations to the uploads directory
                file_path = os.path.join(uploads_dir, os.path.basename(normalized_path))
                logger.warning(f"Redirecting file operation to uploads directory: {file_path}")
            else:
                file_path = absolute_path
            
            # Ensure directory exists for write operations
            if operation in ["write", "append"]:
                directory = os.path.dirname(file_path)
                os.makedirs(directory, exist_ok=True)
            
            # Perform the file operation
            if operation == "read":
                # Check if file exists
                if not os.path.exists(file_path):
                    return StepExecutionResult.error_result(f"File not found: {file_path}")
                
                # Read the file
                async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
                    content = await f.read()
                
                # Determine if content is JSON
                try:
                    json_content = json.loads(content)
                    is_json = True
                except json.JSONDecodeError:
                    json_content = None
                    is_json = False
                
                # Get file metadata
                file_stats = os.stat(file_path)
                file_info = {
                    "path": file_path,
                    "size": file_stats.st_size,
                    "modified": file_stats.st_mtime,
                    "created": file_stats.st_ctime,
                    "is_json": is_json
                }
                
                # Return the file content and metadata
                result = {
                    "content": json_content if is_json else content,
                    "text": content,  # Always include raw text
                    "file_info": file_info
                }
                
                logger.info(f"Read {file_stats.st_size} bytes from {file_path}")
                return StepExecutionResult.success_result(result)
                
            elif operation == "write":
                # Get content to write
                content = inputs.get("content")
                if content is None:
                    return StepExecutionResult.error_result("No content provided for write operation")
                
                # Convert content to string if it's a dict or list
                if isinstance(content, (dict, list)):
                    content = json.dumps(content, indent=2)
                else:
                    content = str(content)
                
                # Write to the file
                async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
                    await f.write(content)
                
                # Get file metadata after writing
                file_stats = os.stat(file_path)
                
                result = {
                    "written": True,
                    "path": file_path,
                    "size": file_stats.st_size
                }
                
                logger.info(f"Wrote {file_stats.st_size} bytes to {file_path}")
                return StepExecutionResult.success_result(result)
                
            elif operation == "append":
                # Get content to append
                content = inputs.get("content")
                if content is None:
                    return StepExecutionResult.error_result("No content provided for append operation")
                
                # Convert content to string if it's a dict or list
                if isinstance(content, (dict, list)):
                    content = json.dumps(content, indent=2)
                else:
                    content = str(content)
                
                # Append to the file
                async with aiofiles.open(file_path, mode='a', encoding='utf-8') as f:
                    await f.write(content)
                
                # Get file metadata after appending
                file_stats = os.stat(file_path)
                
                result = {
                    "appended": True,
                    "path": file_path,
                    "size": file_stats.st_size
                }
                
                logger.info(f"Appended to {file_path}, new size: {file_stats.st_size} bytes")
                return StepExecutionResult.success_result(result)
                
            elif operation == "delete":
                # Check if file exists
                if not os.path.exists(file_path):
                    return StepExecutionResult.error_result(f"File not found: {file_path}")
                
                # Get file metadata before deletion
                file_stats = os.stat(file_path)
                size_before = file_stats.st_size
                
                # Delete the file
                os.remove(file_path)
                
                result = {
                    "deleted": True,
                    "path": file_path,
                    "size_before": size_before
                }
                
                logger.info(f"Deleted file {file_path} ({size_before} bytes)")
                return StepExecutionResult.success_result(result)
                
            elif operation == "list":
                # Get directory contents
                directory = file_path if os.path.isdir(file_path) else os.path.dirname(file_path)
                
                # Check if directory exists
                if not os.path.exists(directory):
                    return StepExecutionResult.error_result(f"Directory not found: {directory}")
                
                # List files and directories
                files = []
                pattern = inputs.get("pattern", "*")
                
                for item in Path(directory).glob(pattern):
                    item_stats = item.stat()
                    files.append({
                        "name": item.name,
                        "path": str(item),
                        "is_dir": item.is_dir(),
                        "size": item_stats.st_size if not item.is_dir() else None,
                        "modified": item_stats.st_mtime,
                        "created": item_stats.st_ctime
                    })
                
                result = {
                    "directory": directory,
                    "pattern": pattern,
                    "files": files,
                    "count": len(files)
                }
                
                logger.info(f"Listed {len(files)} items in {directory} with pattern {pattern}")
                return StepExecutionResult.success_result(result)
                
            else:
                return StepExecutionResult.error_result(
                    f"Unsupported file operation: {operation}. Supported operations: read, write, append, delete, list"
                )
            
        except Exception as e:
            error_msg = f"Error in file step: {str(e)}"
            logger.exception(error_msg)
            return StepExecutionResult.error_result(error_msg)
    
    async def _execute_api_step(
        self,
        step: PipelineStep,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> StepExecutionResult:
        """
        Execute an API step, which calls an external API.
        
        Args:
            step: The pipeline step
            inputs: The resolved inputs for the step
            context: Execution context
            
        Returns:
            StepExecutionResult with API response
        """
        try:
            # Extract required parameters
            url = inputs.get("url")
            if not url:
                return StepExecutionResult.error_result("No URL provided for API step")
            
            method = inputs.get("method", "GET").upper()
            headers = inputs.get("headers", {})
            data = inputs.get("data")
            params = inputs.get("params")
            timeout = inputs.get("timeout", 30)  # Default 30s timeout
            
            # Use httpx for API calls
            import httpx
            import json
            
            # Log the API call (sanitizing any sensitive data)
            logger.info(f"Making {method} request to {url}")
            
            # Make the request
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, params=params)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=data if data else None, params=params)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=data if data else None, params=params)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers, json=data if data else None, params=params)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=data if data else None, params=params)
                else:
                    return StepExecutionResult.error_result(f"Unsupported HTTP method: {method}")
            
            # Process the response
            try:
                response_json = response.json()
                is_json = True
            except (json.JSONDecodeError, ValueError):
                response_json = None
                is_json = False
            
            # Build result
            result = {
                "status": response.status_code,
                "headers": dict(response.headers),
                "is_json": is_json,
                "success": response.status_code < 400
            }
            
            if is_json:
                result["body"] = response_json
            else:
                result["text"] = response.text
            
            # Create metrics
            metrics = {
                "status_code": response.status_code,
                "response_time_ms": response.elapsed.total_seconds() * 1000,
                "content_length": len(response.content)
            }
            
            # Determine success based on status code
            success = response.status_code < 400
            
            # Log details about the response
            logs = [
                {
                    "level": "info" if success else "warning",
                    "message": f"API response: {response.status_code} {response.reason_phrase}"
                }
            ]
            
            if not success:
                # If API call failed, include error information
                error_msg = f"API request failed with status {response.status_code}: {response.reason_phrase}"
                return StepExecutionResult(
                    success=False,
                    outputs=result,
                    error=error_msg,
                    metrics=metrics,
                    logs=logs
                )
            
            return StepExecutionResult(
                success=True,
                outputs=result,
                metrics=metrics,
                logs=logs
            )
            
        except httpx.RequestError as e:
            # Handle network-related errors
            error_msg = f"HTTP request error: {str(e)}"
            logger.exception(error_msg)
            return StepExecutionResult.error_result(error_msg)
        except Exception as e:
            # Handle all other exceptions
            error_msg = f"Error in API step: {str(e)}"
            logger.exception(error_msg)
            return StepExecutionResult.error_result(error_msg)
    
    async def _execute_condition_step(
        self,
        step: PipelineStep,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> StepExecutionResult:
        """
        Execute a condition step, which evaluates a condition.
        
        Args:
            step: The pipeline step
            inputs: The resolved inputs for the step
            context: Execution context
            
        Returns:
            StepExecutionResult with condition evaluation result
        """
        try:
            # Extract required parameters
            condition = inputs.get("condition")
            if not condition:
                return StepExecutionResult.error_result("No condition provided for condition step")
            
            # Get condition configuration
            config = step.config or {}
            condition_type = config.get("condition_type", "expression")
            
            logger.info(f"Evaluating condition: {condition} (type: {condition_type})")
            
            # Evaluate condition based on type
            if condition_type == "expression":
                result = self._evaluate_expression(condition, context)
            elif condition_type == "comparison":
                result = self._evaluate_comparison(condition, context, config)
            elif condition_type == "exists":
                result = self._evaluate_exists(condition, context)
            elif condition_type == "regex":
                result = self._evaluate_regex(condition, context, config)
            else:
                return StepExecutionResult.error_result(f"Unknown condition type: {condition_type}")
            
            return StepExecutionResult.success_result(
                outputs={
                    "result": result, 
                    "condition": condition,
                    "condition_type": condition_type,
                    "evaluation_details": {
                        "condition": condition,
                        "result": result,
                        "context_used": list(context.keys())
                    }
                }
            )
            
        except Exception as e:
            return StepExecutionResult.error_result(f"Error in condition step: {str(e)}")
    
    def _evaluate_expression(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a simple boolean expression with variable substitution."""
        try:
            # Replace variables in condition
            evaluated_condition = self._substitute_variables(condition, context)
            
            # Safe evaluation of simple boolean expressions
            # Only allow specific operators and functions for security
            allowed_names = {
                "__builtins__": {},
                "True": True,
                "False": False,
                "None": None,
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "abs": abs,
                "min": min,
                "max": max,
            }
            
            # Add context variables to allowed names
            for key, value in context.items():
                if isinstance(key, str) and key.isidentifier():
                    allowed_names[key] = value
            
            # Evaluate expression
            result = eval(evaluated_condition, allowed_names)
            return bool(result)
            
        except Exception as e:
            logger.warning(f"Expression evaluation failed: {str(e)}")
            return False
    
    def _evaluate_comparison(self, condition: str, context: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """Evaluate a comparison condition."""
        try:
            left_value = config.get("left_value", "")
            operator = config.get("operator", "==")
            right_value = config.get("right_value", "")
            
            # Substitute variables
            left_resolved = self._substitute_variables(str(left_value), context)
            right_resolved = self._substitute_variables(str(right_value), context)
            
            # Try to convert to appropriate types
            left_val = self._parse_value(left_resolved)
            right_val = self._parse_value(right_resolved)
            
            # Perform comparison
            if operator == "==":
                return left_val == right_val
            elif operator == "!=":
                return left_val != right_val
            elif operator == "<":
                return left_val < right_val
            elif operator == "<=":
                return left_val <= right_val
            elif operator == ">":
                return left_val > right_val
            elif operator == ">=":
                return left_val >= right_val
            elif operator == "contains":
                return str(right_val) in str(left_val)
            elif operator == "starts_with":
                return str(left_val).startswith(str(right_val))
            elif operator == "ends_with":
                return str(left_val).endswith(str(right_val))
            else:
                logger.warning(f"Unknown comparison operator: {operator}")
                return False
                
        except Exception as e:
            logger.warning(f"Comparison evaluation failed: {str(e)}")
            return False
    
    def _evaluate_exists(self, condition: str, context: Dict[str, Any]) -> bool:
        """Check if a variable exists in context."""
        variable_name = condition.strip()
        return variable_name in context and context[variable_name] is not None
    
    def _evaluate_regex(self, condition: str, context: Dict[str, Any], config: Dict[str, Any]) -> bool:
        """Evaluate a regex pattern against a value."""
        try:
            import re
            
            pattern = config.get("pattern", condition)
            target_value = config.get("target_value", "")
            flags = config.get("flags", 0)
            
            # Substitute variables
            target_resolved = self._substitute_variables(str(target_value), context)
            
            # Compile and match regex
            regex = re.compile(pattern, flags)
            return bool(regex.search(target_resolved))
            
        except Exception as e:
            logger.warning(f"Regex evaluation failed: {str(e)}")
            return False
    
    def _parse_value(self, value_str: str):
        """Parse a string value to appropriate type."""
        try:
            # Try to parse as number
            if '.' in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            # Try to parse as boolean
            if value_str.lower() in ['true', 'yes', '1']:
                return True
            elif value_str.lower() in ['false', 'no', '0']:
                return False
            # Return as string
            return value_str
    
    def _substitute_variables(self, text: str, context: Dict[str, Any]) -> str:
        """Substitute variables in text using {{variable}} syntax."""
        import re
        
        def replace_var(match):
            var_name = match.group(1).strip()
            if var_name in context:
                return str(context[var_name])
            return match.group(0)  # Return original if variable not found
        
        # Replace {{variable}} patterns
        return re.sub(r'\{\{([^}]+)\}\}', replace_var, text)
    
    async def _execute_transform_step(
        self,
        step: PipelineStep,
        inputs: Dict[str, Any],
        context: Dict[str, Any]
    ) -> StepExecutionResult:
        """
        Execute a transform step, which transforms data.
        
        Args:
            step: The pipeline step
            inputs: The resolved inputs for the step
            context: Execution context
            
        Returns:
            StepExecutionResult with transformed data
        """
        try:
            # Extract required parameters
            transform_type = inputs.get("transform_type")
            if not transform_type:
                return StepExecutionResult.error_result("No transform_type provided for transform step")
            
            data = inputs.get("data")
            if data is None:
                return StepExecutionResult.error_result("No data provided for transform step")
            
            # Get transform configuration
            config = step.config or {}
            
            logger.info(f"Applying {transform_type} transform to data")
            
            # Apply transformation based on type
            if transform_type == "json_to_text":
                result = self._transform_json_to_text(data, config)
            elif transform_type == "text_to_json":
                result = self._transform_text_to_json(data, config)
            elif transform_type == "json_to_csv":
                result = self._transform_json_to_csv(data, config)
            elif transform_type == "csv_to_json":
                result = self._transform_csv_to_json(data, config)
            elif transform_type == "extract_fields":
                result = self._transform_extract_fields(data, config)
            elif transform_type == "filter_data":
                result = self._transform_filter_data(data, config)
            elif transform_type == "map_values":
                result = self._transform_map_values(data, config)
            elif transform_type == "aggregate":
                result = self._transform_aggregate(data, config)
            elif transform_type == "format_text":
                result = self._transform_format_text(data, config)
            elif transform_type == "custom_script":
                result = self._transform_custom_script(data, config)
            else:
                return StepExecutionResult.error_result(f"Unknown transform type: {transform_type}")
            
            return StepExecutionResult.success_result(
                outputs={
                    "result": result, 
                    "transform_type": transform_type,
                    "original_data_type": type(data).__name__,
                    "result_data_type": type(result).__name__
                }
            )
            
        except Exception as e:
            return StepExecutionResult.error_result(f"Error in transform step: {str(e)}")
    
    def _transform_json_to_text(self, data: Any, config: Dict[str, Any]) -> str:
        """Transform JSON/dict data to formatted text."""
        import json
        
        format_type = config.get("format", "pretty")
        
        if format_type == "pretty":
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format_type == "compact":
            return json.dumps(data, separators=(',', ':'), ensure_ascii=False)
        elif format_type == "template":
            template = config.get("template", "{{data}}")
            return self._substitute_variables(template, {"data": data})
        elif format_type == "key_value":
            if isinstance(data, dict):
                return "\n".join([f"{k}: {v}" for k, v in data.items()])
            else:
                return str(data)
        else:
            return str(data)
    
    def _transform_text_to_json(self, data: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Transform text to JSON object."""
        import json
        import re
        
        parse_type = config.get("parse_type", "auto")
        
        try:
            if parse_type == "json":
                return json.loads(data)
            elif parse_type == "key_value":
                result = {}
                for line in data.strip().split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        result[key.strip()] = value.strip()
                return result
            elif parse_type == "regex":
                pattern = config.get("pattern", r"(\w+):\s*(.+)")
                matches = re.findall(pattern, data)
                return dict(matches)
            else:  # auto
                # Try JSON first
                try:
                    return json.loads(data)
                except:
                    # Fall back to simple parsing
                    return {"text": data, "length": len(data), "word_count": len(data.split())}
        except Exception as e:
            logger.warning(f"Text to JSON parsing failed: {str(e)}")
            return {"text": data, "error": str(e)}
    
    def _transform_json_to_csv(self, data: Any, config: Dict[str, Any]) -> str:
        """Transform JSON data to CSV format."""
        import csv
        import io
        
        if not isinstance(data, list):
            data = [data]
        
        if not data:
            return ""
        
        output = io.StringIO()
        
        # Get field names
        if isinstance(data[0], dict):
            fieldnames = config.get("fields", list(data[0].keys()))
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            for item in data:
                if isinstance(item, dict):
                    writer.writerow(item)
        else:
            writer = csv.writer(output)
            for item in data:
                writer.writerow([item])
        
        return output.getvalue()
    
    def _transform_csv_to_json(self, data: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform CSV data to JSON array."""
        import csv
        import io
        
        try:
            reader = csv.DictReader(io.StringIO(data))
            return list(reader)
        except Exception as e:
            logger.warning(f"CSV to JSON parsing failed: {str(e)}")
            return [{"error": str(e), "raw_data": data}]
    
    def _transform_extract_fields(self, data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract specific fields from data."""
        fields = config.get("fields", [])
        
        if isinstance(data, dict):
            result = {}
            for field in fields:
                if '.' in field:
                    # Nested field access
                    value = self._get_nested_value(data, field.split('.'))
                else:
                    value = data.get(field)
                result[field] = value
            return result
        elif isinstance(data, list) and data and isinstance(data[0], dict):
            # Extract fields from list of objects
            return [self._transform_extract_fields(item, config) for item in data]
        else:
            return {"value": data}
    
    def _transform_filter_data(self, data: Any, config: Dict[str, Any]) -> Any:
        """Filter data based on criteria."""
        if not isinstance(data, list):
            return data
        
        filter_field = config.get("filter_field")
        filter_value = config.get("filter_value")
        filter_operator = config.get("filter_operator", "==")
        
        if not filter_field:
            return data
        
        filtered = []
        for item in data:
            if isinstance(item, dict) and filter_field in item:
                item_value = item[filter_field]
                if self._compare_values(item_value, filter_value, filter_operator):
                    filtered.append(item)
        
        return filtered
    
    def _transform_map_values(self, data: Any, config: Dict[str, Any]) -> Any:
        """Map/transform values using a mapping configuration."""
        mapping = config.get("mapping", {})
        
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                new_key = mapping.get(key, key)
                result[new_key] = value
            return result
        elif isinstance(data, list):
            return [self._transform_map_values(item, config) for item in data]
        else:
            return mapping.get(str(data), data)
    
    def _transform_aggregate(self, data: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Aggregate data using various functions."""
        if not isinstance(data, list):
            return {"error": "Aggregation requires list data"}
        
        agg_field = config.get("field")
        agg_functions = config.get("functions", ["count"])
        
        result = {}
        
        # Basic aggregations
        result["count"] = len(data)
        
        if agg_field and data and isinstance(data[0], dict):
            values = [item.get(agg_field) for item in data if agg_field in item]
            numeric_values = [v for v in values if isinstance(v, (int, float))]
            
            if "sum" in agg_functions and numeric_values:
                result["sum"] = sum(numeric_values)
            if "avg" in agg_functions and numeric_values:
                result["avg"] = sum(numeric_values) / len(numeric_values)
            if "min" in agg_functions and numeric_values:
                result["min"] = min(numeric_values)
            if "max" in agg_functions and numeric_values:
                result["max"] = max(numeric_values)
        
        return result
    
    def _transform_format_text(self, data: Any, config: Dict[str, Any]) -> str:
        """Format data using a template."""
        template = config.get("template", "{{data}}")
        
        if isinstance(data, dict):
            return self._substitute_variables(template, data)
        else:
            return self._substitute_variables(template, {"data": data})
    
    def _transform_custom_script(self, data: Any, config: Dict[str, Any]) -> Any:
        """Execute custom transformation script."""
        script = config.get("script", "")
        if not script:
            return data
        
        try:
            # Safe execution environment
            safe_globals = {
                "__builtins__": {},
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "bool": bool,
                "list": list,
                "dict": dict,
                "abs": abs,
                "min": min,
                "max": max,
                "sum": sum,
                "sorted": sorted,
                "reversed": reversed,
                "data": data,
            }
            
            # Execute script
            local_vars = {}
            exec(script, safe_globals, local_vars)
            
            # Return 'result' variable if exists, otherwise return data
            return local_vars.get("result", data)
            
        except Exception as e:
            logger.warning(f"Custom script execution failed: {str(e)}")
            return {"error": str(e), "original_data": data}
    
    def _get_nested_value(self, data: Dict[str, Any], path: List[str]) -> Any:
        """Get nested value from dictionary using dot notation path."""
        current = data
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _compare_values(self, left: Any, right: Any, operator: str) -> bool:
        """Compare two values using the specified operator."""
        try:
            if operator == "==":
                return left == right
            elif operator == "!=":
                return left != right
            elif operator == "<":
                return left < right
            elif operator == "<=":
                return left <= right
            elif operator == ">":
                return left > right
            elif operator == ">=":
                return left >= right
            elif operator == "contains":
                return str(right) in str(left)
            elif operator == "starts_with":
                return str(left).startswith(str(right))
            elif operator == "ends_with":
                return str(left).endswith(str(right))
            else:
                return False
        except Exception:
            return False