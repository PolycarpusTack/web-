"""
Pydantic schemas for Code Factory Pipeline feature.

This module defines the request and response schemas for the pipeline API,
providing validation and serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum


class PipelineStepTypeEnum(str, Enum):
    """Enum for pipeline step types."""
    PROMPT = "prompt"
    CODE = "code"
    FILE = "file"
    API = "api"
    CONDITION = "condition"
    TRANSFORM = "transform"


class PipelineExecutionStatusEnum(str, Enum):
    """Enum for pipeline execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStepExecutionStatusEnum(str, Enum):
    """Enum for pipeline step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


# --- Pipeline Schemas ---

class PipelineBase(BaseModel):
    """Base schema for pipeline data."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: bool = Field(False)
    tags: Optional[List[str]] = Field(None)
    config: Optional[Dict[str, Any]] = Field(None)


class PipelineCreate(PipelineBase):
    """Schema for creating a new pipeline."""
    pass


class PipelineUpdate(BaseModel):
    """Schema for updating an existing pipeline."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    is_public: Optional[bool] = Field(None)
    tags: Optional[List[str]] = Field(None)
    config: Optional[Dict[str, Any]] = Field(None)
    is_active: Optional[bool] = Field(None)
    version: Optional[str] = Field(None, max_length=20)


class PipelineResponse(PipelineBase):
    """Schema for pipeline response."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    is_active: bool
    version: str
    
    class Config:
        orm_mode = True


# --- Pipeline Step Schemas ---

class PipelineStepBase(BaseModel):
    """Base schema for pipeline step data."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    type: str = Field(..., min_length=1, max_length=50)
    order: int = Field(..., ge=0)
    config: Dict[str, Any] = Field(...)
    input_mapping: Optional[Dict[str, Any]] = Field(None)
    output_mapping: Optional[Dict[str, Any]] = Field(None)
    is_enabled: bool = Field(True)
    timeout: Optional[int] = Field(None, ge=0)
    retry_config: Optional[Dict[str, Any]] = Field(None)
    
    @validator('type')
    def validate_step_type(cls, v):
        """Validate that the step type is supported."""
        if v not in [t.value for t in PipelineStepTypeEnum]:
            raise ValueError(f"Unsupported step type: {v}")
        return v


class PipelineStepCreate(PipelineStepBase):
    """Schema for creating a new pipeline step."""
    pass


class PipelineStepUpdate(BaseModel):
    """Schema for updating an existing pipeline step."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    type: Optional[str] = Field(None, min_length=1, max_length=50)
    order: Optional[int] = Field(None, ge=0)
    config: Optional[Dict[str, Any]] = Field(None)
    input_mapping: Optional[Dict[str, Any]] = Field(None)
    output_mapping: Optional[Dict[str, Any]] = Field(None)
    is_enabled: Optional[bool] = Field(None)
    timeout: Optional[int] = Field(None, ge=0)
    retry_config: Optional[Dict[str, Any]] = Field(None)
    
    @validator('type')
    def validate_step_type(cls, v):
        """Validate that the step type is supported."""
        if v is not None and v not in [t.value for t in PipelineStepTypeEnum]:
            raise ValueError(f"Unsupported step type: {v}")
        return v


class PipelineStepResponse(PipelineStepBase):
    """Schema for pipeline step response."""
    id: str
    pipeline_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        orm_mode = True


class StepOrderItem(BaseModel):
    """Schema for a step order item in a reorder request."""
    step_id: str
    order: int = Field(..., ge=0)


class PipelineStepOrderUpdate(BaseModel):
    """Schema for reordering pipeline steps."""
    steps: List[StepOrderItem] = Field(..., min_items=1)


# --- Pipeline Execution Schemas ---

class PipelineExecuteRequest(BaseModel):
    """Schema for executing a pipeline."""
    input_parameters: Optional[Dict[str, Any]] = Field(None)
    dry_run: bool = Field(False, description="Execute in dry run mode without making actual API calls")
    debug_mode: bool = Field(False, description="Enable debug mode for detailed execution logs")
    step_breakpoints: Optional[List[str]] = Field(None, description="Step IDs to pause execution at")


class PipelineStepExecutionResponse(BaseModel):
    """Schema for pipeline step execution response."""
    id: str
    pipeline_execution_id: str
    step_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    inputs: Optional[Dict[str, Any]] = None
    outputs: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    logs: Optional[List[Dict[str, Any]]] = None
    duration_ms: Optional[int] = None
    metrics: Optional[Dict[str, Any]] = None
    model_id: Optional[str] = None
    
    # Include related objects
    step: Optional[PipelineStepResponse] = None
    
    class Config:
        orm_mode = True


class PipelineExecutionResponse(BaseModel):
    """Schema for pipeline execution response."""
    id: str
    pipeline_id: str
    user_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    input_parameters: Optional[Dict[str, Any]] = None
    results: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    logs: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # Include related objects
    step_executions: Optional[List[PipelineStepExecutionResponse]] = None
    
    class Config:
        orm_mode = True