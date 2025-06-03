"""
Enhanced Pipeline Execution Engine with Provider Integration

This module provides an enhanced pipeline execution engine that integrates
with the new provider abstraction layer for unified AI model access.
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

from providers import (
    get_provider, 
    ProviderType, 
    ProviderCredentials,
    GenerationRequest,
    GenerationResponse,
    Message,
    MessageRole
)
from providers.cost_tracker_db import get_cost_tracker
from providers.base import ProviderError, RateLimitError, AuthenticationError
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
    cost_tracker: Optional[Any] = None


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


class EnhancedLLMStepExecutor:
    """Enhanced LLM executor using the provider abstraction layer."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cost_tracker = get_cost_tracker(db)
    
    async def execute(self, step: PipelineStep, context: ExecutionContext, dry_run: bool = False) -> StepResult:
        """Execute an LLM step using the provider system."""
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
            provider_type = config.get("provider", "openai")
            
            if not model_id:
                return StepResult(
                    success=False,
                    error="Model ID is required for LLM steps"
                )
            
            # Dry run mode - simulate execution without making actual API calls
            if dry_run:
                # Interpolate variables in prompts to validate
                prompt = self._interpolate_variables(prompt_template, context.variables)
                if system_prompt:
                    system_prompt = self._interpolate_variables(system_prompt, context.variables)
                
                # Simulate response
                simulated_response = f"[DRY RUN] LLM Response from {model_id}\nPrompt: {prompt[:100]}..."
                simulated_tokens = len(prompt.split()) + 50  # Rough estimation
                
                return StepResult(
                    success=True,
                    output=simulated_response,
                    execution_time=0.1,  # Simulated time
                    cost=simulated_tokens * 0.00001,  # Simulated cost
                    tokens_used=simulated_tokens,
                    metadata={
                        "model_id": model_id,
                        "provider": provider_type,
                        "prompt_tokens": len(prompt.split()),
                        "completion_tokens": 50,
                        "total_tokens": simulated_tokens,
                        "dry_run": True
                    }
                )
            
            # Get provider credentials from user settings or pipeline config
            credentials = await self._get_provider_credentials(
                provider_type, 
                context.user_id, 
                config
            )
            
            if not credentials:
                return StepResult(
                    success=False,
                    error=f"No credentials found for provider: {provider_type}"
                )
            
            # Interpolate variables in prompts
            prompt = self._interpolate_variables(prompt_template, context.variables)
            if system_prompt:
                system_prompt = self._interpolate_variables(system_prompt, context.variables)
            
            # Create messages for chat-based models
            messages = []
            if system_prompt:
                messages.append(Message(role=MessageRole.SYSTEM, content=system_prompt))
            messages.append(Message(role=MessageRole.USER, content=prompt))
            
            # Create generation request
            request = GenerationRequest(
                messages=messages,
                model=model_id,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                stream=stream,
                response_format=response_format
            )
            
            # Get provider and execute
            async with self._get_provider_context(provider_type, credentials) as provider:
                response = await provider.generate_text(request)
                
                # Record usage for cost tracking
                usage_cost = 0.0
                if response.usage:
                    usage_cost = await self.cost_tracker.record_usage(
                        provider=ProviderType(provider_type),
                        model=model_id,
                        operation="text_generation",
                        input_tokens=response.usage.prompt_tokens,
                        output_tokens=response.usage.completion_tokens,
                        user_id=context.user_id,
                        pipeline_id=context.metadata.get("pipeline_id"),
                        execution_id=context.execution_id
                    )
                
                execution_time = time.time() - start_time
                
                return StepResult(
                    success=True,
                    output=response.content,
                    execution_time=execution_time,
                    cost=usage_cost,
                    tokens_used=response.usage.total_tokens if response.usage else 0,
                    metadata={
                        "model_id": model_id,
                        "provider": provider_type,
                        "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                        "finish_reason": response.finish_reason,
                        "response_time": response.response_time,
                        "function_call": response.function_call,
                        "tool_calls": response.tool_calls
                    }
                )
                
        except AuthenticationError as e:
            return StepResult(
                success=False,
                error=f"Authentication failed for {provider_type}: {e.message}",
                execution_time=time.time() - start_time
            )
        
        except RateLimitError as e:
            return StepResult(
                success=False,
                error=f"Rate limit exceeded for {provider_type}: {e.message}",
                execution_time=time.time() - start_time,
                metadata={"retry_after": e.retry_after}
            )
            
        except ProviderError as e:
            return StepResult(
                success=False,
                error=f"Provider error ({provider_type}): {e.message}",
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.exception(f"Unexpected error in LLM step execution: {e}")
            return StepResult(
                success=False,
                error=f"Unexpected error: {str(e)}",
                execution_time=execution_time
            )
    
    async def _get_provider_credentials(
        self, 
        provider_type: str, 
        user_id: str, 
        config: Dict[str, Any]
    ) -> Optional[ProviderCredentials]:
        """Get provider credentials from user settings or config."""
        try:
            # First check if credentials are in the step config (for testing)
            # WARNING: This is insecure and should only be used for testing
            if "credentials" in config:
                logger.warning(f"Using plaintext credentials from pipeline config for {provider_type} - INSECURE!")
                cred_config = config["credentials"]
                return ProviderCredentials(
                    provider_type=ProviderType(provider_type),
                    api_key=cred_config.get("api_key"),
                    organization_id=cred_config.get("organization_id"),
                    project_id=cred_config.get("project_id"),
                    endpoint=cred_config.get("endpoint")
                )
            
            # Get encrypted credentials from user settings in database
            from db import crud
            from utils.encryption import decrypt_provider_credentials
            
            user_settings = await crud.get_user_settings(self.db, user_id)
            
            if user_settings and user_settings.provider_credentials:
                provider_creds = user_settings.provider_credentials.get(provider_type)
                if provider_creds:
                    try:
                        # Decrypt credentials
                        decrypted = decrypt_provider_credentials(
                            provider_creds.get("encrypted_api_key", ""),
                            provider_creds.get("encrypted_data")
                        )
                        
                        return ProviderCredentials(
                            provider_type=ProviderType(provider_type),
                            api_key=decrypted.get("api_key"),
                            organization_id=decrypted.get("organization_id"),
                            project_id=decrypted.get("project_id"),
                            endpoint=decrypted.get("endpoint")
                        )
                    except Exception as decrypt_error:
                        logger.error(f"Failed to decrypt credentials for {provider_type}: {decrypt_error}")
            
            # Fallback to environment variables
            import os
            if provider_type == "openai":
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    logger.info("Using OpenAI credentials from environment variables")
                    return ProviderCredentials(
                        provider_type=ProviderType.OPENAI,
                        api_key=api_key,
                        organization_id=os.getenv("OPENAI_ORG_ID")
                    )
            elif provider_type == "anthropic":
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if api_key:
                    logger.info("Using Anthropic credentials from environment variables")
                    return ProviderCredentials(
                        provider_type=ProviderType.ANTHROPIC,
                        api_key=api_key
                    )
            elif provider_type == "google":
                api_key = os.getenv("GOOGLE_AI_API_KEY")
                if api_key:
                    logger.info("Using Google AI credentials from environment variables")
                    return ProviderCredentials(
                        provider_type=ProviderType.GOOGLE,
                        api_key=api_key,
                        project_id=os.getenv("GOOGLE_PROJECT_ID")
                    )
            
            logger.warning(f"No credentials found for provider {provider_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting provider credentials: {e}")
            return None
    
    async def _get_provider_context(self, provider_type: str, credentials: ProviderCredentials):
        """Get provider context manager."""
        from providers.registry import get_registry
        registry = get_registry()
        return registry.get_provider_context(ProviderType(provider_type), credentials)
    
    def _interpolate_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """Interpolate variables in template using {{variable}} syntax."""
        if not template:
            return ""
        
        result = template
        for key, value in variables.items():
            # Convert value to string representation
            if isinstance(value, (dict, list)):
                str_value = json.dumps(value, indent=2)
            else:
                str_value = str(value)
            
            # Replace {{key}} with value
            result = result.replace(f"{{{{{key}}}}}", str_value)
        
        return result
    
    async def validate(self, step: PipelineStep) -> List[str]:
        """Validate LLM step configuration."""
        errors = []
        config = step.config
        
        # Required fields
        if not config.get("model_id"):
            errors.append("model_id is required")
        
        if not config.get("prompt"):
            errors.append("prompt is required")
        
        # Validate parameters
        temperature = config.get("temperature", 0.7)
        if not 0 <= temperature <= 2:
            errors.append("temperature must be between 0 and 2")
        
        top_p = config.get("top_p", 1.0)
        if not 0 <= top_p <= 1:
            errors.append("top_p must be between 0 and 1")
        
        max_tokens = config.get("max_tokens", 2048)
        if not isinstance(max_tokens, int) or max_tokens <= 0:
            errors.append("max_tokens must be a positive integer")
        
        # Validate provider
        provider = config.get("provider", "openai")
        valid_providers = ["openai", "anthropic", "google", "ollama"]
        if provider not in valid_providers:
            errors.append(f"provider must be one of: {', '.join(valid_providers)}")
        
        return errors


class EnhancedPipelineExecutor:
    """Enhanced pipeline executor with provider integration."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.cost_tracker = get_cost_tracker(db)
        
        # Register step executors
        self.step_executors = {
            StepType.LLM: EnhancedLLMStepExecutor(db),
            # Add other executors as needed
        }
    
    async def execute_pipeline(
        self,
        pipeline_id: str,
        user_id: str,
        input_parameters: Dict[str, Any],
        context: Optional[ExecutionContext] = None,
        dry_run: bool = False,
        debug_mode: bool = False
    ) -> Dict[str, Any]:
        """Execute a complete pipeline."""
        execution_id = str(uuid.uuid4())
        
        if context is None:
            context = ExecutionContext(
                execution_id=execution_id,
                user_id=user_id,
                variables=input_parameters.copy(),
                start_time=datetime.utcnow(),
                cost_tracker=self.cost_tracker
            )
        
        try:
            # Get pipeline from database
            from db import crud
            pipeline = await crud.get_pipeline(self.db, pipeline_id)
            if not pipeline:
                raise ValueError(f"Pipeline {pipeline_id} not found")
            
            # Get pipeline steps
            steps = await crud.get_pipeline_steps(self.db, pipeline_id)
            if not steps:
                raise ValueError(f"No steps found for pipeline {pipeline_id}")
            
            # Sort steps by order
            steps.sort(key=lambda s: s.order)
            
            context.total_steps = len(steps)
            context.metadata["pipeline_id"] = pipeline_id
            
            # Execute steps sequentially
            total_cost = 0.0
            total_tokens = 0
            step_results = []
            
            for i, step in enumerate(steps):
                if not step.is_enabled:
                    continue
                
                context.step_index = i
                
                # Get appropriate executor
                step_type = StepType(step.type)
                executor = self.step_executors.get(step_type)
                
                if not executor:
                    raise ValueError(f"No executor found for step type: {step.type}")
                
                # Execute step
                result = await executor.execute(step, context, dry_run=dry_run)
                
                # Update totals
                total_cost += result.cost
                total_tokens += result.tokens_used
                
                # Store result
                step_results.append({
                    "step_id": step.id,
                    "step_name": step.name,
                    "success": result.success,
                    "output": result.output,
                    "error": result.error,
                    "execution_time": result.execution_time,
                    "cost": result.cost,
                    "tokens_used": result.tokens_used,
                    "metadata": result.metadata
                })
                
                # Update context variables with step output
                if result.success and result.output is not None:
                    # Add step output to context variables
                    step_name = step.name.lower().replace(" ", "_")
                    context.variables[f"{step_name}_output"] = result.output
                    context.variables[f"step_{i}_output"] = result.output
                
                # Stop execution if step failed
                if not result.success:
                    return {
                        "execution_id": execution_id,
                        "status": ExecutionStatus.FAILED.value,
                        "error": f"Step '{step.name}' failed: {result.error}",
                        "total_cost": total_cost,
                        "total_tokens": total_tokens,
                        "execution_time": (datetime.utcnow() - context.start_time).total_seconds(),
                        "step_results": step_results,
                        "final_output": None
                    }
            
            # Get final output (output of last successful step)
            final_output = step_results[-1]["output"] if step_results else None
            
            return {
                "execution_id": execution_id,
                "status": ExecutionStatus.COMPLETED.value,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "execution_time": (datetime.utcnow() - context.start_time).total_seconds(),
                "step_results": step_results,
                "final_output": final_output
            }
            
        except Exception as e:
            logger.exception(f"Pipeline execution failed: {e}")
            return {
                "execution_id": execution_id,
                "status": ExecutionStatus.FAILED.value,
                "error": str(e),
                "total_cost": 0.0,
                "total_tokens": 0,
                "execution_time": (datetime.utcnow() - context.start_time).total_seconds(),
                "step_results": [],
                "final_output": None
            }