"""
Database models for Code Factory Pipeline feature.

This module defines the models for storing pipeline configurations,
their steps, executions, and related data.
"""

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, DateTime, Text, JSON, Float, Table, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from enum import Enum as PyEnum
from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime

from .database import Base
from .models import generate_uuid


class PipelineStepType(PyEnum):
    """Types of pipeline steps."""
    PROMPT = "prompt"  # A simple prompt to the LLM
    CODE = "code"      # Code execution (e.g., Python)
    FILE = "file"      # File input/output
    API = "api"        # External API call
    CONDITION = "condition"  # Conditional branching
    TRANSFORM = "transform"  # Data transformation


class PipelineExecutionStatus(PyEnum):
    """Status of pipeline executions."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PipelineStepExecutionStatus(PyEnum):
    """Status of individual pipeline step executions."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Pipeline(Base):
    """
    Model for storing pipeline configurations.
    
    A pipeline is a sequence of steps that are executed in order,
    with outputs from previous steps available as inputs to later steps.
    """
    __tablename__ = "pipelines"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    version = Column(String, default="1.0")
    tags = Column(JSON, nullable=True)  # Array of string tags
    config = Column(JSON, nullable=True)  # Additional configuration options
    
    # Relationships
    user = relationship("User", back_populates="pipelines")
    steps = relationship("PipelineStep", back_populates="pipeline", 
                         cascade="all, delete-orphan", order_by="PipelineStep.order")
    executions = relationship("PipelineExecution", back_populates="pipeline", 
                              cascade="all, delete-orphan")


class PipelineStep(Base):
    """
    Model for storing individual steps within a pipeline.
    
    Each step has a type, configuration, and position within the pipeline.
    Steps can reference outputs from previous steps as inputs.
    """
    __tablename__ = "pipeline_steps"

    id = Column(String, primary_key=True, default=generate_uuid)
    pipeline_id = Column(String, ForeignKey("pipelines.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String, nullable=False)  # Corresponds to PipelineStepType
    order = Column(Integer, nullable=False)  # Position in the pipeline sequence
    config = Column(JSON, nullable=False)  # Step-specific configuration
    input_mapping = Column(JSON, nullable=True)  # Maps previous step outputs to this step's inputs
    output_mapping = Column(JSON, nullable=True)  # Defines how outputs are named for use by later steps
    is_enabled = Column(Boolean, default=True)
    timeout = Column(Integer, nullable=True)  # Timeout in seconds, null means no timeout
    retry_config = Column(JSON, nullable=True)  # Retry configuration (attempts, delay, etc.)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    pipeline = relationship("Pipeline", back_populates="steps")
    executions = relationship("PipelineStepExecution", back_populates="step", 
                              cascade="all, delete-orphan")


class PipelineExecution(Base):
    """
    Model for tracking pipeline executions.
    
    Each execution represents a single run of a pipeline,
    with its own set of step executions, input parameters, and results.
    """
    __tablename__ = "pipeline_executions"

    id = Column(String, primary_key=True, default=generate_uuid)
    pipeline_id = Column(String, ForeignKey("pipelines.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False, default=PipelineExecutionStatus.PENDING.value)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    input_parameters = Column(JSON, nullable=True)  # User-provided input parameters
    results = Column(JSON, nullable=True)  # Final pipeline results
    error = Column(Text, nullable=True)  # Error message if failed
    duration_ms = Column(Integer, nullable=True)  # Total execution time in milliseconds
    logs = Column(JSON, nullable=True)  # Log messages (array of objects)
    meta_data = Column(JSON, nullable=True)  # Additional metadata
    
    # Relationships
    pipeline = relationship("Pipeline", back_populates="executions")
    user = relationship("User")
    step_executions = relationship("PipelineStepExecution", back_populates="pipeline_execution", 
                                  cascade="all, delete-orphan", order_by="PipelineStepExecution.started_at")


class PipelineStepExecution(Base):
    """
    Model for tracking individual step executions within a pipeline run.
    
    Each step execution captures the inputs, outputs, and performance metrics
    for a single step within a pipeline execution.
    """
    __tablename__ = "pipeline_step_executions"

    id = Column(String, primary_key=True, default=generate_uuid)
    pipeline_execution_id = Column(String, ForeignKey("pipeline_executions.id"), nullable=False)
    step_id = Column(String, ForeignKey("pipeline_steps.id"), nullable=False)
    status = Column(String, nullable=False, default=PipelineStepExecutionStatus.PENDING.value)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    inputs = Column(JSON, nullable=True)  # Inputs to this step execution
    outputs = Column(JSON, nullable=True)  # Outputs from this step execution
    error = Column(Text, nullable=True)  # Error message if failed
    logs = Column(JSON, nullable=True)  # Log messages specific to this step execution
    duration_ms = Column(Integer, nullable=True)  # Execution time in milliseconds
    metrics = Column(JSON, nullable=True)  # Performance metrics (tokens, cost, etc.)
    model_id = Column(String, ForeignKey("models.id"), nullable=True)  # If step uses an LLM model
    
    # Relationships
    pipeline_execution = relationship("PipelineExecution", back_populates="step_executions")
    step = relationship("PipelineStep", back_populates="executions")
    model = relationship("Model", foreign_keys=[model_id])


# Extend User model to include pipelines relationship
from .models import User
User.pipelines = relationship("Pipeline", back_populates="user", cascade="all, delete-orphan")