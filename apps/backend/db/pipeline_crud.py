"""
CRUD operations for Code Factory Pipeline feature.

This module provides database access functions for managing pipelines,
their steps, executions, and related data.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload, joinedload
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from .pipeline_models import (
    Pipeline, PipelineStep, PipelineExecution, PipelineStepExecution,
    PipelineExecutionStatus, PipelineStepExecutionStatus
)


# --- Pipeline CRUD Operations ---

async def create_pipeline(
    db: AsyncSession,
    user_id: str,
    name: str,
    description: Optional[str] = None,
    is_public: bool = False,
    tags: Optional[List[str]] = None,
    config: Optional[Dict[str, Any]] = None
) -> Pipeline:
    """Create a new pipeline."""
    pipeline = Pipeline(
        user_id=user_id,
        name=name,
        description=description,
        is_public=is_public,
        tags=tags,
        config=config
    )
    db.add(pipeline)
    await db.commit()
    await db.refresh(pipeline)
    return pipeline


async def get_pipeline(db: AsyncSession, pipeline_id: str) -> Optional[Pipeline]:
    """Get a pipeline by ID, including its steps."""
    query = (
        select(Pipeline)
        .where(Pipeline.id == pipeline_id)
        .options(
            # Load steps eagerly
            selectinload(Pipeline.steps)
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_pipelines(
    db: AsyncSession,
    user_id: Optional[str] = None,
    include_public: bool = True,
    tags: Optional[List[str]] = None,
    skip: int = 0,
    limit: int = 20,
    include_steps: bool = False
) -> List[Pipeline]:
    """
    Get pipelines with filters.
    
    Args:
        db: Database session
        user_id: Optional user ID to filter by ownership
        include_public: Whether to include public pipelines
        tags: Optional list of tags to filter by
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        include_steps: Whether to include steps in the query
        
    Returns:
        List of Pipeline objects with optional related data
    """
    query = select(Pipeline)
    
    # Apply filters
    conditions = []
    
    # User filter with public option
    if user_id:
        if include_public:
            conditions.append(or_(
                Pipeline.user_id == user_id,
                Pipeline.is_public == True
            ))
        else:
            conditions.append(Pipeline.user_id == user_id)
    elif not include_public:
        # If no user_id is provided and include_public is False, return empty list
        return []
    
    # Tag filter (if any tags match)
    if tags and len(tags) > 0:
        # Using JSONB containment operator for PostgreSQL
        # For SQLite we need a different approach
        # This is a simplified version that works for basic usage
        for tag in tags:
            conditions.append(Pipeline.tags.contains([tag]))
    
    # Apply conditions if any
    if conditions:
        query = query.where(and_(*conditions))
    
    # Active pipelines only
    query = query.where(Pipeline.is_active == True)
    
    # Add eager loading if requested
    if include_steps:
        query = query.options(selectinload(Pipeline.steps))
    
    # Add sorting and pagination
    query = query.order_by(desc(Pipeline.updated_at)).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    return result.scalars().all()


async def update_pipeline(
    db: AsyncSession,
    pipeline_id: str,
    data: Dict[str, Any]
) -> Optional[Pipeline]:
    """Update a pipeline."""
    # Ensure updated_at is set
    data['updated_at'] = datetime.now()
    
    await db.execute(
        update(Pipeline)
        .where(Pipeline.id == pipeline_id)
        .values(**data)
    )
    await db.commit()
    
    return await get_pipeline(db, pipeline_id)


async def delete_pipeline(db: AsyncSession, pipeline_id: str) -> bool:
    """Delete a pipeline (steps and executions are cascade deleted)."""
    # First check if pipeline exists
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        return False
    
    # Delete the pipeline
    await db.execute(
        delete(Pipeline)
        .where(Pipeline.id == pipeline_id)
    )
    await db.commit()
    return True


# --- Pipeline Step CRUD Operations ---

async def create_pipeline_step(
    db: AsyncSession,
    pipeline_id: str,
    name: str,
    step_type: str,
    order: int,
    config: Dict[str, Any],
    description: Optional[str] = None,
    input_mapping: Optional[Dict[str, Any]] = None,
    output_mapping: Optional[Dict[str, Any]] = None,
    is_enabled: bool = True,
    timeout: Optional[int] = None,
    retry_config: Optional[Dict[str, Any]] = None
) -> PipelineStep:
    """Create a new pipeline step."""
    step = PipelineStep(
        pipeline_id=pipeline_id,
        name=name,
        type=step_type,
        order=order,
        config=config,
        description=description,
        input_mapping=input_mapping,
        output_mapping=output_mapping,
        is_enabled=is_enabled,
        timeout=timeout,
        retry_config=retry_config
    )
    db.add(step)
    await db.commit()
    await db.refresh(step)
    return step


async def get_pipeline_steps(
    db: AsyncSession,
    pipeline_id: str,
    include_disabled: bool = False
) -> List[PipelineStep]:
    """Get all steps for a pipeline."""
    query = (
        select(PipelineStep)
        .where(PipelineStep.pipeline_id == pipeline_id)
    )
    
    if not include_disabled:
        query = query.where(PipelineStep.is_enabled == True)
    
    query = query.order_by(PipelineStep.order)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_pipeline_step(db: AsyncSession, step_id: str) -> Optional[PipelineStep]:
    """Get a pipeline step by ID."""
    query = select(PipelineStep).where(PipelineStep.id == step_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_pipeline_step(
    db: AsyncSession,
    step_id: str,
    data: Dict[str, Any]
) -> Optional[PipelineStep]:
    """Update a pipeline step."""
    # Ensure updated_at is set
    data['updated_at'] = datetime.now()
    
    await db.execute(
        update(PipelineStep)
        .where(PipelineStep.id == step_id)
        .values(**data)
    )
    await db.commit()
    
    return await get_pipeline_step(db, step_id)


async def delete_pipeline_step(db: AsyncSession, step_id: str) -> bool:
    """Delete a pipeline step."""
    # First check if step exists
    step = await get_pipeline_step(db, step_id)
    if not step:
        return False
    
    # Delete the step
    await db.execute(
        delete(PipelineStep)
        .where(PipelineStep.id == step_id)
    )
    await db.commit()
    return True


async def reorder_pipeline_steps(
    db: AsyncSession,
    pipeline_id: str,
    step_order: List[Tuple[str, int]]
) -> bool:
    """
    Reorder pipeline steps.
    
    Args:
        db: Database session
        pipeline_id: Pipeline ID
        step_order: List of (step_id, new_order) tuples
        
    Returns:
        True if successful, False otherwise
    """
    try:
        for step_id, order in step_order:
            await db.execute(
                update(PipelineStep)
                .where(and_(
                    PipelineStep.id == step_id,
                    PipelineStep.pipeline_id == pipeline_id
                ))
                .values(order=order)
            )
        
        await db.commit()
        return True
    except Exception:
        await db.rollback()
        return False


# --- Pipeline Execution CRUD Operations ---

async def create_pipeline_execution(
    db: AsyncSession,
    pipeline_id: str,
    user_id: str,
    input_parameters: Optional[Dict[str, Any]] = None
) -> PipelineExecution:
    """Create a new pipeline execution."""
    execution = PipelineExecution(
        pipeline_id=pipeline_id,
        user_id=user_id,
        status=PipelineExecutionStatus.PENDING.value,
        input_parameters=input_parameters
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    return execution


async def get_pipeline_execution(db: AsyncSession, execution_id: str) -> Optional[PipelineExecution]:
    """Get a pipeline execution by ID, including step executions."""
    query = (
        select(PipelineExecution)
        .where(PipelineExecution.id == execution_id)
        .options(
            # Load step executions eagerly
            selectinload(PipelineExecution.step_executions)
            .joinedload(PipelineStepExecution.step)
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_pipeline_executions(
    db: AsyncSession,
    pipeline_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    include_step_executions: bool = False
) -> List[PipelineExecution]:
    """
    Get pipeline executions with filters.
    
    Args:
        db: Database session
        pipeline_id: Optional pipeline ID to filter by
        user_id: Optional user ID to filter by
        status: Optional status to filter by
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        include_step_executions: Whether to include step executions
        
    Returns:
        List of PipelineExecution objects with optional related data
    """
    query = select(PipelineExecution)
    
    # Apply filters
    conditions = []
    
    if pipeline_id:
        conditions.append(PipelineExecution.pipeline_id == pipeline_id)
    
    if user_id:
        conditions.append(PipelineExecution.user_id == user_id)
    
    if status:
        conditions.append(PipelineExecution.status == status)
    
    # Apply conditions if any
    if conditions:
        query = query.where(and_(*conditions))
    
    # Add eager loading if requested
    if include_step_executions:
        query = query.options(
            selectinload(PipelineExecution.step_executions)
            .joinedload(PipelineStepExecution.step)
        )
    
    # Add sorting and pagination
    query = query.order_by(desc(PipelineExecution.started_at)).offset(skip).limit(limit)
    
    # Execute query
    result = await db.execute(query)
    return result.scalars().all()


async def update_pipeline_execution(
    db: AsyncSession,
    execution_id: str,
    data: Dict[str, Any]
) -> Optional[PipelineExecution]:
    """Update a pipeline execution."""
    await db.execute(
        update(PipelineExecution)
        .where(PipelineExecution.id == execution_id)
        .values(**data)
    )
    await db.commit()
    
    return await get_pipeline_execution(db, execution_id)


async def complete_pipeline_execution(
    db: AsyncSession,
    execution_id: str,
    status: PipelineExecutionStatus,
    results: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
) -> Optional[PipelineExecution]:
    """Mark a pipeline execution as completed, with results or error."""
    now = datetime.now()
    
    # Calculate duration
    execution = await get_pipeline_execution(db, execution_id)
    if not execution:
        return None
    
    duration_ms = None
    if execution.started_at:
        duration_ms = int((now - execution.started_at).total_seconds() * 1000)
    
    data = {
        'status': status.value,
        'completed_at': now,
        'duration_ms': duration_ms
    }
    
    if results is not None:
        data['results'] = results
    
    if error is not None:
        data['error'] = error
    
    return await update_pipeline_execution(db, execution_id, data)


# --- Pipeline Step Execution CRUD Operations ---

async def create_pipeline_step_execution(
    db: AsyncSession,
    pipeline_execution_id: str,
    step_id: str,
    inputs: Optional[Dict[str, Any]] = None,
    model_id: Optional[str] = None
) -> PipelineStepExecution:
    """Create a new pipeline step execution."""
    step_execution = PipelineStepExecution(
        pipeline_execution_id=pipeline_execution_id,
        step_id=step_id,
        status=PipelineStepExecutionStatus.PENDING.value,
        inputs=inputs,
        model_id=model_id
    )
    db.add(step_execution)
    await db.commit()
    await db.refresh(step_execution)
    return step_execution


async def get_pipeline_step_execution(db: AsyncSession, step_execution_id: str) -> Optional[PipelineStepExecution]:
    """Get a pipeline step execution by ID."""
    query = (
        select(PipelineStepExecution)
        .where(PipelineStepExecution.id == step_execution_id)
        .options(
            joinedload(PipelineStepExecution.step),
            joinedload(PipelineStepExecution.model)
        )
    )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def update_pipeline_step_execution(
    db: AsyncSession,
    step_execution_id: str,
    data: Dict[str, Any]
) -> Optional[PipelineStepExecution]:
    """Update a pipeline step execution."""
    await db.execute(
        update(PipelineStepExecution)
        .where(PipelineStepExecution.id == step_execution_id)
        .values(**data)
    )
    await db.commit()
    
    return await get_pipeline_step_execution(db, step_execution_id)


async def complete_pipeline_step_execution(
    db: AsyncSession,
    step_execution_id: str,
    status: PipelineStepExecutionStatus,
    outputs: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    metrics: Optional[Dict[str, Any]] = None
) -> Optional[PipelineStepExecution]:
    """Mark a pipeline step execution as completed, with outputs or error."""
    now = datetime.now()
    
    # Calculate duration
    step_execution = await get_pipeline_step_execution(db, step_execution_id)
    if not step_execution:
        return None
    
    duration_ms = None
    if step_execution.started_at:
        duration_ms = int((now - step_execution.started_at).total_seconds() * 1000)
    
    data = {
        'status': status.value,
        'completed_at': now,
        'duration_ms': duration_ms
    }
    
    if outputs is not None:
        data['outputs'] = outputs
    
    if error is not None:
        data['error'] = error
    
    if metrics is not None:
        data['metrics'] = metrics
    
    return await update_pipeline_step_execution(db, step_execution_id, data)


async def append_step_execution_log(
    db: AsyncSession,
    step_execution_id: str,
    log_entry: Dict[str, Any]
) -> bool:
    """Append a log entry to a step execution's logs."""
    step_execution = await get_pipeline_step_execution(db, step_execution_id)
    if not step_execution:
        return False
    
    # Initialize logs if needed
    logs = step_execution.logs or []
    
    # Add timestamp if not provided
    if 'timestamp' not in log_entry:
        log_entry['timestamp'] = datetime.now().isoformat()
    
    # Append the new log entry
    logs.append(log_entry)
    
    # Update the step execution
    await update_pipeline_step_execution(db, step_execution_id, {'logs': logs})
    return True