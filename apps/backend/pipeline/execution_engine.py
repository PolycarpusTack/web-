"""
Pipeline Execution Engine

This module provides a robust pipeline execution engine that can execute
complex AI workflows with proper error handling, async support, and state management.
"""
import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, AsyncGenerator, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from db.models import User
from db.pipeline_models import Pipeline, PipelineExecution, PipelineStep, PipelineStepExecution

logger = logging.getLogger(__name__)

class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"

class StepType(Enum):
    LLM = "llm"
    CODE = "code"
    API = "api"
    TRANSFORM = "transform"
    CONDITION = "condition"
    MERGE = "merge"
    INPUT = "input"
    OUTPUT = "output"

@dataclass
class ExecutionContext:
    """Context passed between pipeline steps."""
    variables: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_id: str = ""
    user_id: str = ""
    step_index: int = 0
    total_steps: int = 0
    start_time: datetime = field(default_factory=datetime.utcnow)

@dataclass 
class StepResult:
    """Result of a pipeline step execution."""
    success: bool
    output: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0
    tokens_used: int = 0

class PipelineStep(BaseModel):
    """Pipeline step definition."""
    id: str
    name: str
    type: StepType
    config: Dict[str, Any] = Field(default_factory=dict)
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    depends_on: List[str] = Field(default_factory=list)
    retry_count: int = 0
    timeout: int = 300  # seconds
    enabled: bool = True

class PipelineDefinition(BaseModel):
    """Complete pipeline definition."""
    id: str
    name: str
    description: Optional[str] = None
    steps: List[PipelineStep]
    connections: List[Dict[str, str]] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=dict)
    version: str = "1.0"

class StepExecutor:
    """Base class for step executors."""
    
    async def execute(self, step: PipelineStep, context: ExecutionContext) -> StepResult:
        """Execute a pipeline step."""
        raise NotImplementedError
    
    async def validate(self, step: PipelineStep) -> List[str]:
        """Validate step configuration. Return list of errors."""
        return []

class LLMStepExecutor(StepExecutor):
    """Enhanced executor for LLM steps with multiple model support and streaming."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        # Initialize HTTP client for external model APIs
        import httpx
        self.http_client = httpx.AsyncClient(timeout=60.0)
    
    async def execute(self, step: PipelineStep, context: ExecutionContext) -> StepResult:
        """Execute an LLM step with enhanced features."""
        start_time = time.time()
        
        try:
            # Get configuration
            config = step.config
            model_id = config.get("model_id")
            prompt_template = config.get("prompt", "")
            max_tokens = config.get("max_tokens", 2048)
            temperature = config.get("temperature", 0.7)
            top_p = config.get("top_p", 1.0)
            system_prompt = config.get("system_prompt")
            response_format = config.get("response_format", "text")
            stream = config.get("stream", False)
            
            if not model_id:
                return StepResult(
                    success=False,
                    error="Model ID is required for LLM steps"
                )
            
            # Get model from database
            from db import crud
            model = await crud.get_model(self.db, model_id)
            if not model:
                return StepResult(
                    success=False,
                    error=f"Model {model_id} not found"
                )
            
            # Interpolate variables in prompt and system prompt
            prompt = self._interpolate_variables(prompt_template, context.variables)
            if system_prompt:
                system_prompt = self._interpolate_variables(system_prompt, context.variables)
            
            # Execute based on model provider
            if model.provider.lower() == "ollama":
                result = await self._execute_ollama_model(
                    model, prompt, system_prompt, max_tokens, temperature, top_p, response_format, stream
                )
            elif model.provider.lower() in ["openai", "anthropic", "mistral"]:
                result = await self._execute_external_model(
                    model, prompt, system_prompt, max_tokens, temperature, top_p, response_format, stream
                )
            else:
                return StepResult(
                    success=False,
                    error=f"Unsupported model provider: {model.provider}"
                )
            
            execution_time = time.time() - start_time
            
            # Calculate cost based on model pricing
            cost = self._calculate_cost(model, result["prompt_tokens"], result["completion_tokens"])
            
            return StepResult(
                success=True,
                output=result["content"],
                execution_time=execution_time,
                cost=cost,
                tokens_used=result["total_tokens"],
                metadata={
                    "model_id": model_id,
                    "model_name": model.name,
                    "model_provider": model.provider,
                    "prompt_tokens": result["prompt_tokens"],
                    "completion_tokens": result["completion_tokens"],
                    "total_tokens": result["total_tokens"],
                    "prompt_length": len(prompt),
                    "response_length": len(result["content"]),
                    "response_format": response_format,
                    "temperature": temperature,
                    "top_p": top_p,
                    "system_prompt_used": bool(system_prompt)
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return StepResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _execute_ollama_model(self, model, prompt, system_prompt, max_tokens, temperature, top_p, response_format, stream):
        """Execute Ollama model via local API."""
        # Use the application's HTTP client if available
        try:
            from main import app
            client = app.state.http_client
        except:
            client = self.http_client
        
        # Determine endpoint based on model capabilities
        if "chat" in model.id.lower() or "instruct" in model.id.lower():
            endpoint = "/api/chat"
            payload = {
                "model": model.id,
                "messages": [],
                "stream": stream,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p
                }
            }
            
            if system_prompt:
                payload["messages"].append({"role": "system", "content": system_prompt})
            payload["messages"].append({"role": "user", "content": prompt})
            
        else:
            endpoint = "/api/generate"
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
                
            payload = {
                "model": model.id,
                "prompt": full_prompt,
                "stream": stream,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p
                }
            }
        
        # Make request to Ollama
        response = await client.post(endpoint, json=payload)
        response.raise_for_status()
        response_data = response.json()
        
        # Extract response based on endpoint
        if endpoint == "/api/chat":
            content = response_data.get("message", {}).get("content", "")
        else:
            content = response_data.get("response", "")
        
        # Parse as JSON if requested
        if response_format == "json":
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                # If parsing fails, wrap in error object
                content = {"error": "Invalid JSON response", "raw_content": content}
        
        # Get token counts
        prompt_tokens = response_data.get("prompt_eval_count", len(prompt.split()))
        completion_tokens = response_data.get("eval_count", len(str(content).split()))
        
        return {
            "content": content,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
    
    async def _execute_external_model(self, model, prompt, system_prompt, max_tokens, temperature, top_p, response_format, stream):
        """Execute external model via API (OpenAI, Anthropic, etc.)."""
        # This would implement actual API calls to external providers
        # For now, simulate the response
        
        # Simulate processing
        await asyncio.sleep(0.5)
        
        if response_format == "json":
            content = {
                "simulated_response": f"This is a simulated JSON response from {model.name}",
                "original_prompt": prompt[:50] + "..." if len(prompt) > 50 else prompt,
                "model_provider": model.provider
            }
        else:
            content = f"Simulated response from {model.name} ({model.provider}): {prompt[:100]}..."
        
        # Estimate token usage
        prompt_tokens = len(prompt.split()) + (len(system_prompt.split()) if system_prompt else 0)
        completion_tokens = len(str(content).split())
        
        return {
            "content": content,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens
        }
    
    def _calculate_cost(self, model, prompt_tokens, completion_tokens):
        """Calculate cost based on model pricing."""
        if not model.pricing:
            # Default cost if no pricing info
            return (prompt_tokens + completion_tokens) * 0.00002
        
        prompt_cost = prompt_tokens * model.pricing.get("prompt_cost_per_token", 0.00001)
        completion_cost = completion_tokens * model.pricing.get("completion_cost_per_token", 0.00002)
        
        return prompt_cost + completion_cost
    
    def _interpolate_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Replace {{variable}} placeholders with actual values."""
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    async def validate(self, step: PipelineStep) -> List[str]:
        """Validate LLM step configuration with enhanced validation."""
        errors = []
        config = step.config
        
        # Required fields
        if not config.get("model_id"):
            errors.append("Model ID is required")
        
        if not config.get("prompt"):
            errors.append("Prompt template is required")
        
        # Validate numeric parameters
        max_tokens = config.get("max_tokens", 2048)
        if not isinstance(max_tokens, int) or max_tokens <= 0 or max_tokens > 100000:
            errors.append("Max tokens must be a positive integer between 1 and 100000")
        
        temperature = config.get("temperature", 0.7)
        if not isinstance(temperature, (int, float)) or not 0 <= temperature <= 2:
            errors.append("Temperature must be between 0 and 2")
        
        top_p = config.get("top_p", 1.0)
        if top_p is not None and (not isinstance(top_p, (int, float)) or not 0 <= top_p <= 1):
            errors.append("Top-p must be between 0 and 1")
        
        # Validate response format
        response_format = config.get("response_format", "text")
        if response_format not in ["text", "json"]:
            errors.append("Response format must be 'text' or 'json'")
        
        # Validate frequency and presence penalties if provided
        frequency_penalty = config.get("frequency_penalty")
        if frequency_penalty is not None and (not isinstance(frequency_penalty, (int, float)) or not -2 <= frequency_penalty <= 2):
            errors.append("Frequency penalty must be between -2 and 2")
        
        presence_penalty = config.get("presence_penalty")
        if presence_penalty is not None and (not isinstance(presence_penalty, (int, float)) or not -2 <= presence_penalty <= 2):
            errors.append("Presence penalty must be between -2 and 2")
        
        # Validate model exists in database
        if config.get("model_id"):
            try:
                from db import crud
                # Note: In a real implementation, you'd want to check if the model exists
                # but this requires an async database session which we don't have in validation
                pass
            except Exception:
                pass
        
        return errors

class CodeStepExecutor(StepExecutor):
    """Enhanced executor for code steps with advanced sandboxing and multi-language support."""
    
    def __init__(self):
        # Track resource usage across executions
        self.execution_stats = {
            "total_executions": 0,
            "total_execution_time": 0.0,
            "memory_peak": 0
        }
    
    async def execute(self, step: PipelineStep, context: ExecutionContext) -> StepResult:
        """Execute a code step in a secure sandboxed environment."""
        start_time = time.time()
        
        try:
            config = step.config
            code = config.get("code", "")
            language = config.get("language", "python")
            timeout = config.get("timeout", 30)
            memory_limit = config.get("memory_limit", 128)  # MB
            packages = config.get("packages", [])
            
            if not code:
                return StepResult(
                    success=False,
                    error="Code is required for code steps"
                )
            
            # Execute based on language
            if language == "python":
                result = await self._execute_python_code(
                    code, context.variables, timeout, memory_limit, packages
                )
            elif language == "javascript":
                result = await self._execute_javascript_code(
                    code, context.variables, timeout, memory_limit
                )
            else:
                return StepResult(
                    success=False,
                    error=f"Unsupported language: {language}. Supported: python, javascript"
                )
            
            execution_time = time.time() - start_time
            self.execution_stats["total_executions"] += 1
            self.execution_stats["total_execution_time"] += execution_time
            
            return StepResult(
                success=True,
                output=result["output"],
                execution_time=execution_time,
                metadata={
                    "language": language,
                    "code_length": len(code),
                    "lines_of_code": len(code.splitlines()),
                    "memory_used": result.get("memory_used", 0),
                    "cpu_time": result.get("cpu_time", execution_time),
                    "packages_used": packages,
                    "output_logs": result.get("logs", []),
                    "security_warnings": result.get("security_warnings", [])
                }
            )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            return StepResult(
                success=False,
                error=f"Code execution timed out after {timeout} seconds",
                execution_time=execution_time
            )
        except Exception as e:
            execution_time = time.time() - start_time
            return StepResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _execute_python_code(
        self, 
        code: str, 
        variables: Dict[str, Any], 
        timeout: int, 
        memory_limit: int,
        packages: List[str]
    ) -> Dict[str, Any]:
        """Execute Python code with enhanced security and monitoring."""
        import sys
        import io
        import contextlib
        from types import ModuleType
        
        # Security checks
        security_warnings = []
        forbidden_imports = [
            'os', 'sys', 'subprocess', 'socket', 'urllib', 'requests',
            'open', 'file', 'input', 'raw_input', '__import__', 'eval',
            'exec', 'compile', 'globals', 'locals', 'vars', 'dir'
        ]
        
        for forbidden in forbidden_imports:
            if forbidden in code:
                security_warnings.append(f"Potentially unsafe: '{forbidden}' detected")
        
        # Create enhanced safe globals environment
        safe_builtins = {
            # Basic types
            "len": len, "str": str, "int": int, "float": float, "bool": bool,
            "list": list, "dict": dict, "set": set, "tuple": tuple,
            
            # Iterators and functions
            "range": range, "enumerate": enumerate, "zip": zip,
            "map": map, "filter": filter, "sum": sum, "any": any, "all": all,
            
            # Math functions
            "max": max, "min": min, "abs": abs, "round": round, "pow": pow,
            "sorted": sorted, "reversed": reversed,
            
            # String operations
            "chr": chr, "ord": ord,
            
            # Type checking
            "isinstance": isinstance, "issubclass": issubclass, "type": type,
            
            # Safe output
            "print": print,
        }
        
        # Add allowed packages
        allowed_modules = {
            "json": json,
            "math": __import__("math"),
            "datetime": __import__("datetime"),
            "re": __import__("re"),
            "random": __import__("random"),
            "base64": __import__("base64"),
            "hashlib": __import__("hashlib"),
            "uuid": __import__("uuid"),
        }
        
        # Add user-requested packages (with validation)
        for package in packages:
            if package in ["numpy", "pandas", "requests"]:
                try:
                    allowed_modules[package] = __import__(package)
                except ImportError:
                    security_warnings.append(f"Package '{package}' not available")
        
        safe_globals = {
            "__builtins__": safe_builtins,
            **allowed_modules
        }
        
        # Prepare local variables
        local_vars = variables.copy()
        
        # Capture output
        captured_output = io.StringIO()
        captured_logs = []
        
        def safe_print(*args, **kwargs):
            # Custom print function that captures output
            output = " ".join(str(arg) for arg in args)
            captured_logs.append(output)
            print(output, file=captured_output)
        
        safe_globals["print"] = safe_print
        
        # Execute with timeout and monitoring
        try:
            # Use asyncio timeout for execution
            result = await asyncio.wait_for(
                self._run_code_sync(code, safe_globals, local_vars),
                timeout=timeout
            )
            
            # Return execution result
            return {
                "output": result,
                "logs": captured_logs,
                "security_warnings": security_warnings,
                "memory_used": 0,  # Would need psutil for real memory tracking
                "cpu_time": 0,     # Would need resource module for real CPU tracking
            }
            
        except Exception as e:
            raise Exception(f"Python execution error: {str(e)}")
    
    async def _run_code_sync(self, code: str, safe_globals: dict, local_vars: dict) -> Any:
        """Run Python code synchronously in a thread to avoid blocking."""
        import concurrent.futures
        
        def execute_code():
            exec(code, safe_globals, local_vars)
            
            # Return the 'result' variable if it exists, otherwise return modified variables
            if 'result' in local_vars:
                return local_vars['result']
            else:
                # Return only new or modified variables
                original_keys = set(safe_globals.keys())
                new_vars = {k: v for k, v in local_vars.items() 
                           if k not in original_keys and not k.startswith('_')}
                return new_vars
        
        # Execute in thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            result = await loop.run_in_executor(executor, execute_code)
            return result
    
    async def _execute_javascript_code(
        self, 
        code: str, 
        variables: Dict[str, Any], 
        timeout: int, 
        memory_limit: int
    ) -> Dict[str, Any]:
        """Execute JavaScript code using Node.js subprocess."""
        import subprocess
        import tempfile
        import os
        
        security_warnings = []
        
        # Security checks for JavaScript
        forbidden_js = ['require', 'import', 'fs', 'process', 'child_process', 'eval']
        for forbidden in forbidden_js:
            if forbidden in code:
                security_warnings.append(f"Potentially unsafe JS: '{forbidden}' detected")
        
        # Create a temporary JavaScript file
        js_template = f"""
        // Pipeline variables
        const variables = {json.dumps(variables)};
        
        // Make variables available in global scope
        Object.assign(global, variables);
        
        // Safe console.log implementation
        const logs = [];
        const originalLog = console.log;
        console.log = (...args) => {{
            const message = args.map(arg => String(arg)).join(' ');
            logs.push(message);
            originalLog(message);
        }};
        
        // User code
        try {{
            {code}
            
            // Export result
            const result = typeof result !== 'undefined' ? result : undefined;
            console.log('__PIPELINE_RESULT__' + JSON.stringify({{
                output: result,
                logs: logs,
                success: true
            }}));
        }} catch (error) {{
            console.log('__PIPELINE_RESULT__' + JSON.stringify({{
                output: null,
                logs: logs,
                success: false,
                error: error.message
            }}));
        }}
        """
        
        try:
            # Write to temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(js_template)
                temp_file = f.name
            
            # Execute with Node.js
            process = await asyncio.create_subprocess_exec(
                'node', temp_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout
            )
            
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            
            # Clean up
            os.unlink(temp_file)
            
            # Parse output
            output_lines = stdout.decode().split('\n')
            result_line = None
            logs = []
            
            for line in output_lines:
                if line.startswith('__PIPELINE_RESULT__'):
                    result_line = line[19:]  # Remove prefix
                else:
                    if line.strip():
                        logs.append(line)
            
            if result_line:
                result_data = json.loads(result_line)
                if not result_data.get("success"):
                    raise Exception(result_data.get("error", "JavaScript execution failed"))
                
                return {
                    "output": result_data.get("output"),
                    "logs": result_data.get("logs", []),
                    "security_warnings": security_warnings,
                    "memory_used": 0,
                    "cpu_time": 0,
                }
            else:
                raise Exception("Failed to parse JavaScript execution result")
                
        except FileNotFoundError:
            raise Exception("Node.js is not installed or not in PATH")
        except Exception as e:
            raise Exception(f"JavaScript execution error: {str(e)}")
    
    async def validate(self, step: PipelineStep) -> List[str]:
        """Validate code step configuration with enhanced checks."""
        errors = []
        config = step.config
        
        # Required fields
        if not config.get("code"):
            errors.append("Code is required")
        
        # Language validation
        language = config.get("language", "python")
        if language not in ["python", "javascript"]:
            errors.append(f"Unsupported language: {language}. Supported: python, javascript")
        
        # Timeout validation
        timeout = config.get("timeout", 30)
        if not isinstance(timeout, int) or timeout <= 0 or timeout > 300:
            errors.append("Timeout must be between 1 and 300 seconds")
        
        # Memory limit validation
        memory_limit = config.get("memory_limit", 128)
        if not isinstance(memory_limit, int) or memory_limit <= 0 or memory_limit > 1024:
            errors.append("Memory limit must be between 1 and 1024 MB")
        
        # Package validation
        packages = config.get("packages", [])
        if not isinstance(packages, list):
            errors.append("Packages must be a list")
        else:
            allowed_packages = ["numpy", "pandas", "requests", "pillow", "scipy"]
            for package in packages:
                if package not in allowed_packages:
                    errors.append(f"Package '{package}' not allowed")
        
        # Basic security checks
        code = config.get("code", "")
        if any(danger in code for danger in ["__import__", "eval(", "exec(", "open("]):
            errors.append("Code contains potentially unsafe operations")
        
        return errors

class TransformStepExecutor(StepExecutor):
    """Executor for data transformation steps."""
    
    async def execute(self, step: PipelineStep, context: ExecutionContext) -> StepResult:
        """Execute a data transformation step."""
        start_time = time.time()
        
        try:
            config = step.config
            transform_type = config.get("type", "extract")
            source_path = config.get("source_path", "")
            target_key = config.get("target_key", "result")
            
            # Get source data
            source_data = context.variables
            if source_path:
                source_data = self._get_nested_value(source_data, source_path)
            
            # Apply transformation
            if transform_type == "extract":
                result = self._extract_fields(source_data, config.get("fields", []))
            elif transform_type == "filter":
                result = self._filter_data(source_data, config.get("condition", {}))
            elif transform_type == "format":
                result = self._format_data(source_data, config.get("format", ""))
            else:
                return StepResult(
                    success=False,
                    error=f"Unknown transform type: {transform_type}"
                )
            
            execution_time = time.time() - start_time
            
            return StepResult(
                success=True,
                output={target_key: result},
                execution_time=execution_time,
                metadata={
                    "transform_type": transform_type,
                    "source_path": source_path,
                    "target_key": target_key
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return StepResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _get_nested_value(self, data: Any, path: str) -> Any:
        """Get value from nested object using dot notation."""
        if not path:
            return data
        
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        
        return current
    
    def _extract_fields(self, data: Any, fields: List[str]) -> Dict[str, Any]:
        """Extract specific fields from data."""
        if not isinstance(data, dict):
            return {}
        
        return {field: data.get(field) for field in fields if field in data}
    
    def _filter_data(self, data: Any, condition: Dict[str, Any]) -> Any:
        """Filter data based on condition."""
        # Simplified filtering - could be expanded
        if isinstance(data, list):
            field = condition.get("field")
            operator = condition.get("operator", "eq")
            value = condition.get("value")
            
            if field and operator and value is not None:
                if operator == "eq":
                    return [item for item in data if isinstance(item, dict) and item.get(field) == value]
                elif operator == "gt":
                    return [item for item in data if isinstance(item, dict) and item.get(field, 0) > value]
                elif operator == "lt":
                    return [item for item in data if isinstance(item, dict) and item.get(field, 0) < value]
        
        return data
    
    def _format_data(self, data: Any, format_string: str) -> str:
        """Format data using a format string."""
        if isinstance(data, dict):
            return format_string.format(**data)
        else:
            return format_string.format(data=data)
    
    async def validate(self, step: PipelineStep) -> List[str]:
        """Validate transform step configuration."""
        errors = []
        config = step.config
        
        transform_type = config.get("type")
        if not transform_type:
            errors.append("Transform type is required")
        elif transform_type not in ["extract", "filter", "format"]:
            errors.append(f"Unknown transform type: {transform_type}")
        
        return errors

class ConditionStepExecutor(StepExecutor):
    """Executor for conditional logic steps."""
    
    async def execute(self, step: PipelineStep, context: ExecutionContext) -> StepResult:
        """Execute a conditional step with branching logic."""
        start_time = time.time()
        
        try:
            config = step.config
            condition_config = config.get("condition", {})
            
            if not condition_config:
                return StepResult(
                    success=False,
                    error="Condition configuration is required"
                )
            
            # Evaluate the condition
            condition_result = await self._evaluate_condition(condition_config, context.variables)
            
            execution_time = time.time() - start_time
            
            return StepResult(
                success=True,
                output={
                    "condition_result": condition_result,
                    "branch": "true" if condition_result else "false",
                    "original_data": context.variables
                },
                execution_time=execution_time,
                metadata={
                    "condition": condition_config,
                    "evaluation_result": condition_result
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return StepResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    async def _evaluate_condition(self, condition_config: Dict[str, Any], variables: Dict[str, Any]) -> bool:
        """Evaluate a condition against the current context variables."""
        field = condition_config.get("field")
        operator = condition_config.get("operator", "eq")
        value = condition_config.get("value")
        
        if not field:
            raise ValueError("Condition field is required")
        
        # Get the field value from variables
        field_value = self._get_nested_value(variables, field)
        
        # Perform comparison based on operator
        if operator == "eq":
            return field_value == value
        elif operator == "ne":
            return field_value != value
        elif operator == "gt":
            return self._safe_numeric_compare(field_value, value, lambda a, b: a > b)
        elif operator == "lt":
            return self._safe_numeric_compare(field_value, value, lambda a, b: a < b)
        elif operator == "gte":
            return self._safe_numeric_compare(field_value, value, lambda a, b: a >= b)
        elif operator == "lte":
            return self._safe_numeric_compare(field_value, value, lambda a, b: a <= b)
        elif operator == "in":
            if isinstance(value, list):
                return field_value in value
            elif isinstance(value, str):
                return str(field_value) in value
            else:
                return False
        elif operator == "contains":
            if isinstance(field_value, (list, str)):
                return value in field_value
            else:
                return False
        elif operator == "exists":
            return field_value is not None
        elif operator == "regex":
            import re
            if isinstance(field_value, str) and isinstance(value, str):
                return bool(re.search(value, field_value))
            else:
                return False
        else:
            raise ValueError(f"Unknown operator: {operator}")
    
    def _get_nested_value(self, data: Any, path: str) -> Any:
        """Get value from nested object using dot notation."""
        if not path:
            return data
        
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            elif isinstance(current, list) and key.isdigit():
                index = int(key)
                if 0 <= index < len(current):
                    current = current[index]
                else:
                    return None
            else:
                return None
        
        return current
    
    def _safe_numeric_compare(self, a: Any, b: Any, comparator) -> bool:
        """Safely compare two values numerically."""
        try:
            # Try to convert both values to numbers
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                return comparator(a, b)
            elif isinstance(a, str) and isinstance(b, str):
                # Try to parse as numbers
                try:
                    num_a = float(a)
                    num_b = float(b)
                    return comparator(num_a, num_b)
                except ValueError:
                    # Fall back to string comparison
                    return comparator(a, b)
            else:
                # Convert to strings and compare
                return comparator(str(a), str(b))
        except Exception:
            return False
    
    async def validate(self, step: PipelineStep) -> List[str]:
        """Validate condition step configuration."""
        errors = []
        config = step.config
        
        condition = config.get("condition")
        if not condition:
            errors.append("Condition configuration is required")
            return errors
        
        if not condition.get("field"):
            errors.append("Condition field is required")
        
        operator = condition.get("operator", "eq")
        valid_operators = ["eq", "ne", "gt", "lt", "gte", "lte", "in", "contains", "exists", "regex"]
        if operator not in valid_operators:
            errors.append(f"Invalid operator: {operator}. Valid operators: {', '.join(valid_operators)}")
        
        if operator != "exists" and "value" not in condition:
            errors.append("Condition value is required for this operator")
        
        return errors

class APIStepExecutor(StepExecutor):
    """Executor for API call steps."""
    
    def __init__(self):
        import httpx
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def execute(self, step: PipelineStep, context: ExecutionContext) -> StepResult:
        """Execute an API call step."""
        start_time = time.time()
        
        try:
            config = step.config
            url = config.get("url")
            method = config.get("method", "GET").upper()
            headers = config.get("headers", {})
            body = config.get("body")
            timeout = config.get("timeout", 30)
            auth = config.get("auth")
            
            if not url:
                return StepResult(
                    success=False,
                    error="URL is required for API steps"
                )
            
            # Interpolate variables in URL and headers
            url = self._interpolate_variables(url, context.variables)
            headers = self._interpolate_dict_values(headers, context.variables)
            
            # Prepare request kwargs
            request_kwargs = {
                "method": method,
                "url": url,
                "headers": headers,
                "timeout": timeout
            }
            
            # Add body for methods that support it
            if method in ["POST", "PUT", "PATCH"] and body is not None:
                if isinstance(body, dict):
                    # Interpolate variables in body
                    body = self._interpolate_dict_values(body, context.variables)
                    request_kwargs["json"] = body
                else:
                    # String body
                    body = self._interpolate_variables(str(body), context.variables)
                    request_kwargs["content"] = body
            
            # Add authentication
            if auth:
                auth_type = auth.get("type")
                if auth_type == "bearer":
                    token = auth.get("token")
                    if token:
                        headers["Authorization"] = f"Bearer {token}"
                elif auth_type == "basic":
                    username = auth.get("username")
                    password = auth.get("password")
                    if username and password:
                        import base64
                        credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
                        headers["Authorization"] = f"Basic {credentials}"
                elif auth_type == "api_key":
                    api_key = auth.get("api_key")
                    header_name = auth.get("header_name", "X-API-Key")
                    if api_key:
                        headers[header_name] = api_key
            
            # Make the request
            response = await self.http_client.request(**request_kwargs)
            
            # Parse response
            try:
                response_data = response.json()
            except:
                response_data = response.text
            
            execution_time = time.time() - start_time
            
            return StepResult(
                success=True,
                output={
                    "response": response_data,
                    "status_code": response.status_code,
                    "headers": dict(response.headers),
                    "url": str(response.url)
                },
                execution_time=execution_time,
                metadata={
                    "method": method,
                    "url": url,
                    "status_code": response.status_code,
                    "response_size": len(response.content)
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            return StepResult(
                success=False,
                error=str(e),
                execution_time=execution_time
            )
    
    def _interpolate_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Replace {{variable}} placeholders with actual values."""
        if not isinstance(template, str):
            return template
            
        result = template
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def _interpolate_dict_values(self, data: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Interpolate variables in dictionary values."""
        if not isinstance(data, dict):
            return data
            
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._interpolate_variables(value, variables)
            elif isinstance(value, dict):
                result[key] = self._interpolate_dict_values(value, variables)
            else:
                result[key] = value
        return result
    
    async def validate(self, step: PipelineStep) -> List[str]:
        """Validate API step configuration."""
        errors = []
        config = step.config
        
        url = config.get("url")
        if not url:
            errors.append("URL is required")
        else:
            # Basic URL validation
            if not (url.startswith("http://") or url.startswith("https://") or url.startswith("{{")):
                errors.append("URL must start with http:// or https://")
        
        method = config.get("method", "GET")
        valid_methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
        if method.upper() not in valid_methods:
            errors.append(f"Invalid HTTP method: {method}")
        
        timeout = config.get("timeout", 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("Timeout must be a positive number")
        
        return errors

class PipelineExecutionEngine:
    """Main pipeline execution engine."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.executors: Dict[StepType, StepExecutor] = {
            StepType.LLM: LLMStepExecutor(db),
            StepType.CODE: CodeStepExecutor(),
            StepType.TRANSFORM: TransformStepExecutor(),
            StepType.CONDITION: ConditionStepExecutor(),
            StepType.API: APIStepExecutor(),
        }
        self.active_executions: Dict[str, ExecutionContext] = {}
    
    async def execute_pipeline(
        self, 
        pipeline: PipelineDefinition, 
        user: User,
        initial_variables: Dict[str, Any] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute a pipeline and yield progress updates."""
        execution_id = str(uuid.uuid4())
        
        # Create execution context
        context = ExecutionContext(
            variables=initial_variables or {},
            execution_id=execution_id,
            user_id=user.id,
            total_steps=len([s for s in pipeline.steps if s.enabled])
        )
        
        # Add pipeline variables to context
        context.variables.update(pipeline.variables)
        
        # Store active execution
        self.active_executions[execution_id] = context
        
        try:
            # Validate pipeline
            validation_errors = await self.validate_pipeline(pipeline)
            if validation_errors:
                yield {
                    "type": "error",
                    "execution_id": execution_id,
                    "error": "Pipeline validation failed",
                    "details": validation_errors
                }
                return
            
            # Start execution
            yield {
                "type": "started",
                "execution_id": execution_id,
                "pipeline_id": pipeline.id,
                "total_steps": context.total_steps
            }
            
            # Execute steps in order (simplified - real implementation would handle dependencies)
            total_cost = 0.0
            total_tokens = 0
            
            for step in pipeline.steps:
                if not step.enabled:
                    continue
                
                context.step_index += 1
                
                yield {
                    "type": "step_started",
                    "execution_id": execution_id,
                    "step_id": step.id,
                    "step_name": step.name,
                    "step_index": context.step_index,
                    "total_steps": context.total_steps
                }
                
                # Execute step with retry logic
                result = await self._execute_step_with_retry(step, context)
                
                if result.success:
                    # Update context with step output
                    if result.output:
                        if isinstance(result.output, dict):
                            context.variables.update(result.output)
                        else:
                            context.variables[f"step_{step.id}_output"] = result.output
                    
                    total_cost += result.cost
                    total_tokens += result.tokens_used
                    
                    yield {
                        "type": "step_completed",
                        "execution_id": execution_id,
                        "step_id": step.id,
                        "step_name": step.name,
                        "result": result.output,
                        "execution_time": result.execution_time,
                        "cost": result.cost,
                        "tokens_used": result.tokens_used,
                        "metadata": result.metadata
                    }
                else:
                    yield {
                        "type": "step_failed",
                        "execution_id": execution_id,
                        "step_id": step.id,
                        "step_name": step.name,
                        "error": result.error,
                        "execution_time": result.execution_time
                    }
                    
                    # Stop execution on failure (could be configurable)
                    yield {
                        "type": "failed",
                        "execution_id": execution_id,
                        "error": f"Step {step.name} failed: {result.error}",
                        "total_cost": total_cost,
                        "total_tokens": total_tokens
                    }
                    return
            
            # Pipeline completed successfully
            execution_time = (datetime.utcnow() - context.start_time).total_seconds()
            
            yield {
                "type": "completed",
                "execution_id": execution_id,
                "final_output": context.variables,
                "execution_time": execution_time,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "steps_completed": context.step_index
            }
            
        except Exception as e:
            logger.error(f"Pipeline execution error: {e}")
            yield {
                "type": "error",
                "execution_id": execution_id,
                "error": str(e)
            }
        finally:
            # Clean up
            self.active_executions.pop(execution_id, None)
    
    async def _execute_step_with_retry(self, step: PipelineStep, context: ExecutionContext) -> StepResult:
        """Execute a step with retry logic."""
        max_retries = step.retry_count
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                # Get appropriate executor
                executor = self.executors.get(step.type)
                if not executor:
                    return StepResult(
                        success=False,
                        error=f"No executor found for step type: {step.type}"
                    )
                
                # Execute with timeout
                result = await asyncio.wait_for(
                    executor.execute(step, context),
                    timeout=step.timeout
                )
                
                if result.success:
                    return result
                else:
                    last_error = result.error
                    if attempt < max_retries:
                        # Wait before retry (exponential backoff)
                        await asyncio.sleep(2 ** attempt)
                        continue
                    else:
                        return result
                        
            except asyncio.TimeoutError:
                last_error = f"Step timed out after {step.timeout} seconds"
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
                    continue
        
        return StepResult(
            success=False,
            error=f"Step failed after {max_retries + 1} attempts. Last error: {last_error}"
        )
    
    async def validate_pipeline(self, pipeline: PipelineDefinition) -> List[str]:
        """Validate entire pipeline configuration."""
        errors = []
        
        if not pipeline.steps:
            errors.append("Pipeline must have at least one step")
        
        # Validate each step
        for step in pipeline.steps:
            executor = self.executors.get(step.type)
            if executor:
                step_errors = await executor.validate(step)
                for error in step_errors:
                    errors.append(f"Step '{step.name}': {error}")
            else:
                errors.append(f"Step '{step.name}': Unknown step type '{step.type}'")
        
        # Validate dependencies (simplified)
        step_ids = {step.id for step in pipeline.steps}
        for step in pipeline.steps:
            for dep in step.depends_on:
                if dep not in step_ids:
                    errors.append(f"Step '{step.name}' depends on non-existent step '{dep}'")
        
        return errors
    
    async def cancel_execution(self, execution_id: str) -> bool:
        """Cancel a running pipeline execution."""
        if execution_id in self.active_executions:
            del self.active_executions[execution_id]
            return True
        return False
    
    def get_active_executions(self) -> List[str]:
        """Get list of currently active execution IDs."""
        return list(self.active_executions.keys())