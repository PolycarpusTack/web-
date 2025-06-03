"""
Pipeline Execution API

This module provides REST endpoints for pipeline execution and monitoring.
"""
import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from db.database import get_db
from db.models import User
from auth.jwt import get_current_user
from pipeline.execution_engine import (
    PipelineExecutionEngine, 
    PipelineDefinition, 
    ExecutionStatus,
    StepType
)

router = APIRouter(prefix="/api/pipeline/execution", tags=["Pipeline Execution"])

# Request/Response Models
class ExecutePipelineRequest(BaseModel):
    pipeline: PipelineDefinition
    initial_variables: Dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    debug_mode: bool = False

class ExecutionStatusResponse(BaseModel):
    execution_id: str
    status: ExecutionStatus
    pipeline_id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None
    total_cost: float = 0.0
    total_tokens: int = 0
    steps_completed: int = 0
    total_steps: int = 0
    final_output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ValidatePipelineRequest(BaseModel):
    pipeline: PipelineDefinition

class ValidationResponse(BaseModel):
    valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

class StepTemplateResponse(BaseModel):
    type: StepType
    name: str
    description: str
    default_config: Dict[str, Any]
    required_fields: List[str]
    optional_fields: List[str]

# Global execution engine instance
execution_engines: Dict[str, PipelineExecutionEngine] = {}

def get_execution_engine(db: AsyncSession = Depends(get_db)) -> PipelineExecutionEngine:
    """Get or create execution engine for this session."""
    engine_id = id(db)  # Use session ID as key
    if engine_id not in execution_engines:
        execution_engines[engine_id] = PipelineExecutionEngine(db)
    return execution_engines[engine_id]

@router.post("/execute")
async def execute_pipeline(
    request: ExecutePipelineRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    engine: PipelineExecutionEngine = Depends(get_execution_engine)
):
    """
    Execute a pipeline and return real-time progress updates via Server-Sent Events.
    """
    if request.dry_run:
        # Validate pipeline without executing
        validation_errors = await engine.validate_pipeline(request.pipeline)
        if validation_errors:
            return {
                "valid": False,
                "errors": validation_errors,
                "message": "Pipeline validation failed"
            }
        else:
            return {
                "valid": True,
                "message": "Pipeline is valid and ready for execution"
            }
    
    async def generate_events():
        """Generate Server-Sent Events for pipeline execution."""
        try:
            async for event in engine.execute_pipeline(
                request.pipeline, 
                current_user, 
                request.initial_variables
            ):
                # Format as SSE
                event_data = json.dumps(event)
                yield f"data: {event_data}\n\n"
                
                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)
                
        except Exception as e:
            error_event = {
                "type": "error",
                "error": str(e),
                "execution_id": "unknown"
            }
            yield f"data: {json.dumps(error_event)}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.post("/validate")
async def validate_pipeline(
    request: ValidatePipelineRequest,
    engine: PipelineExecutionEngine = Depends(get_execution_engine)
) -> ValidationResponse:
    """
    Validate a pipeline configuration without executing it.
    """
    try:
        errors = await engine.validate_pipeline(request.pipeline)
        
        # Separate errors and warnings (simplified - could be more sophisticated)
        validation_errors = [e for e in errors if "error" in e.lower() or "required" in e.lower()]
        warnings = [e for e in errors if e not in validation_errors]
        
        return ValidationResponse(
            valid=len(validation_errors) == 0,
            errors=validation_errors,
            warnings=warnings
        )
        
    except Exception as e:
        return ValidationResponse(
            valid=False,
            errors=[f"Validation error: {str(e)}"],
            warnings=[]
        )

@router.get("/templates/steps")
async def get_step_templates() -> List[StepTemplateResponse]:
    """
    Get available step templates with their default configurations.
    """
    templates = [
        StepTemplateResponse(
            type=StepType.LLM,
            name="LLM Chat",
            description="Execute a language model with advanced configuration",
            default_config={
                "model_id": "",
                "prompt": "{{input}}",
                "system_prompt": "",
                "max_tokens": 2048,
                "temperature": 0.7,
                "top_p": 1.0,
                "frequency_penalty": 0.0,
                "presence_penalty": 0.0,
                "response_format": "text",
                "stream": False
            },
            required_fields=["model_id", "prompt"],
            optional_fields=[
                "system_prompt", "max_tokens", "temperature", "top_p", 
                "frequency_penalty", "presence_penalty", "response_format", "stream"
            ]
        ),
        StepTemplateResponse(
            type=StepType.CODE,
            name="Code Execution",
            description="Execute Python or JavaScript code with secure sandboxing",
            default_config={
                "code": "# Access pipeline variables and set result\n# Available variables: all pipeline variables\n# Set 'result' variable for output\n\nresult = input_data",
                "language": "python",
                "timeout": 30,
                "memory_limit": 128,
                "packages": []
            },
            required_fields=["code"],
            optional_fields=["language", "timeout", "memory_limit", "packages"]
        ),
        StepTemplateResponse(
            type=StepType.TRANSFORM,
            name="Data Transform",
            description="Transform and manipulate data",
            default_config={
                "type": "extract",
                "source_path": "",
                "target_key": "result",
                "fields": []
            },
            required_fields=["type"],
            optional_fields=["source_path", "target_key", "fields", "condition", "format"]
        ),
        StepTemplateResponse(
            type=StepType.API,
            name="API Call",
            description="Make HTTP API requests",
            default_config={
                "url": "",
                "method": "GET",
                "headers": {},
                "timeout": 30
            },
            required_fields=["url", "method"],
            optional_fields=["headers", "body", "timeout", "auth"]
        ),
        StepTemplateResponse(
            type=StepType.CONDITION,
            name="Conditional Branch",
            description="Branch execution based on conditions",
            default_config={
                "condition": {
                    "field": "",
                    "operator": "eq",
                    "value": ""
                },
                "true_branch": [],
                "false_branch": []
            },
            required_fields=["condition"],
            optional_fields=["true_branch", "false_branch"]
        )
    ]
    
    return templates

@router.get("/executions/active")
async def get_active_executions(
    current_user: User = Depends(get_current_user),
    engine: PipelineExecutionEngine = Depends(get_execution_engine)
) -> List[str]:
    """
    Get list of currently active execution IDs for the current user.
    """
    # Note: In a real implementation, you'd filter by user
    return engine.get_active_executions()

@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    engine: PipelineExecutionEngine = Depends(get_execution_engine)
):
    """
    Cancel a running pipeline execution.
    """
    success = await engine.cancel_execution(execution_id)
    
    if success:
        return {"message": f"Execution {execution_id} cancelled successfully"}
    else:
        raise HTTPException(404, f"Execution {execution_id} not found or already completed")

@router.get("/health")
async def execution_health_check(
    engine: PipelineExecutionEngine = Depends(get_execution_engine)
):
    """
    Get execution engine health status.
    """
    active_executions = engine.get_active_executions()
    
    return {
        "status": "healthy",
        "active_executions": len(active_executions),
        "available_executors": list(engine.executors.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }