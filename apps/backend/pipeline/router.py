"""
API Router for Code Factory Pipeline feature.

This module provides the FastAPI routes for creating, managing,
and executing pipelines.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from db.database import get_db
from db.pipeline_models import Pipeline, PipelineStep
from db.pipeline_crud import (
    create_pipeline, get_pipeline, get_pipelines, update_pipeline, delete_pipeline,
    create_pipeline_step, get_pipeline_step, get_pipeline_steps, update_pipeline_step, 
    delete_pipeline_step, reorder_pipeline_steps, get_pipeline_executions
)
from pipeline.engine import PipelineEngine, PipelineExecutionError
from pipeline.enhanced_execution_engine import EnhancedPipelineExecutor
from pipeline.schemas import (
    PipelineCreate, PipelineUpdate, PipelineResponse, PipelineStepCreate, 
    PipelineStepUpdate, PipelineStepResponse, PipelineExecutionResponse,
    PipelineExecuteRequest, PipelineStepOrderUpdate
)
from auth.jwt import get_current_user, get_current_active_user
from db.models import User

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/pipelines",
    tags=["pipelines"],
    responses={404: {"description": "Not found"}},
)


# --- Pipeline Routes ---

@router.post("", response_model=PipelineResponse, status_code=201)
async def create_new_pipeline(
    pipeline_data: PipelineCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new pipeline.
    
    This endpoint creates a new pipeline configuration with the specified
    name, description, and other settings.
    """
    try:
        pipeline = await create_pipeline(
            db=db,
            user_id=current_user.id,
            name=pipeline_data.name,
            description=pipeline_data.description,
            is_public=pipeline_data.is_public,
            tags=pipeline_data.tags,
            config=pipeline_data.config
        )
        return pipeline
    except Exception as e:
        logger.exception("Error creating pipeline")
        raise HTTPException(status_code=500, detail=f"Failed to create pipeline: {str(e)}")


@router.get("", response_model=List[PipelineResponse])
async def list_pipelines(
    tags: Optional[List[str]] = Query(None),
    include_public: bool = Query(True),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List pipelines.
    
    This endpoint returns a list of pipelines that are accessible to the user.
    """
    try:
        pipelines = await get_pipelines(
            db=db,
            user_id=current_user.id,
            include_public=include_public,
            tags=tags,
            skip=skip,
            limit=limit
        )
        return pipelines
    except Exception as e:
        logger.exception("Error listing pipelines")
        raise HTTPException(status_code=500, detail=f"Failed to list pipelines: {str(e)}")


@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline_by_id(
    pipeline_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a pipeline by ID.
    
    This endpoint returns a pipeline by its unique identifier.
    """
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check access permission
    if pipeline.user_id != current_user.id and not pipeline.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to access this pipeline")
    
    return pipeline


@router.put("/{pipeline_id}", response_model=PipelineResponse)
async def update_pipeline_by_id(
    pipeline_data: PipelineUpdate,
    pipeline_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a pipeline.
    
    This endpoint updates an existing pipeline with new configuration.
    """
    # Check if pipeline exists
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check ownership
    if pipeline.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this pipeline")
    
    # Update pipeline
    try:
        updated_pipeline = await update_pipeline(
            db=db,
            pipeline_id=pipeline_id,
            data=pipeline_data.dict(exclude_unset=True)
        )
        return updated_pipeline
    except Exception as e:
        logger.exception("Error updating pipeline")
        raise HTTPException(status_code=500, detail=f"Failed to update pipeline: {str(e)}")


@router.delete("/{pipeline_id}", status_code=204)
async def delete_pipeline_by_id(
    pipeline_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a pipeline.
    
    This endpoint deletes a pipeline and all its steps and executions.
    """
    # Check if pipeline exists
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check ownership
    if pipeline.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this pipeline")
    
    # Delete pipeline
    try:
        success = await delete_pipeline(db, pipeline_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete pipeline")
    except Exception as e:
        logger.exception("Error deleting pipeline")
        raise HTTPException(status_code=500, detail=f"Failed to delete pipeline: {str(e)}")


# --- Pipeline Step Routes ---

@router.post("/{pipeline_id}/steps", response_model=PipelineStepResponse, status_code=201)
async def create_pipeline_step_endpoint(
    step_data: PipelineStepCreate,
    pipeline_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new pipeline step.
    
    This endpoint creates a new step for an existing pipeline.
    """
    # Check if pipeline exists
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check ownership
    if pipeline.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this pipeline")
    
    # Create step
    try:
        step = await create_pipeline_step(
            db=db,
            pipeline_id=pipeline_id,
            name=step_data.name,
            step_type=step_data.type,
            order=step_data.order,
            config=step_data.config,
            description=step_data.description,
            input_mapping=step_data.input_mapping,
            output_mapping=step_data.output_mapping,
            is_enabled=step_data.is_enabled,
            timeout=step_data.timeout,
            retry_config=step_data.retry_config
        )
        return step
    except Exception as e:
        logger.exception("Error creating pipeline step")
        raise HTTPException(status_code=500, detail=f"Failed to create pipeline step: {str(e)}")


@router.get("/{pipeline_id}/steps", response_model=List[PipelineStepResponse])
async def list_pipeline_steps(
    pipeline_id: str = Path(...),
    include_disabled: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List steps for a pipeline.
    
    This endpoint returns a list of steps for a specific pipeline.
    """
    # Check if pipeline exists
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check access permission
    if pipeline.user_id != current_user.id and not pipeline.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to access this pipeline")
    
    # Get steps
    try:
        steps = await get_pipeline_steps(
            db=db,
            pipeline_id=pipeline_id,
            include_disabled=include_disabled
        )
        return steps
    except Exception as e:
        logger.exception("Error listing pipeline steps")
        raise HTTPException(status_code=500, detail=f"Failed to list pipeline steps: {str(e)}")


@router.get("/{pipeline_id}/steps/{step_id}", response_model=PipelineStepResponse)
async def get_pipeline_step_by_id(
    pipeline_id: str = Path(...),
    step_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a pipeline step by ID.
    
    This endpoint returns a specific step of a pipeline.
    """
    # Check if pipeline exists
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check access permission
    if pipeline.user_id != current_user.id and not pipeline.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to access this pipeline")
    
    # Get step
    step = await get_pipeline_step(db, step_id)
    if not step or step.pipeline_id != pipeline_id:
        raise HTTPException(status_code=404, detail="Pipeline step not found")
    
    return step


@router.put("/{pipeline_id}/steps/{step_id}", response_model=PipelineStepResponse)
async def update_pipeline_step_by_id(
    step_data: PipelineStepUpdate,
    pipeline_id: str = Path(...),
    step_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a pipeline step.
    
    This endpoint updates an existing pipeline step with new configuration.
    """
    # Check if pipeline exists
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check ownership
    if pipeline.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this pipeline")
    
    # Check if step exists
    step = await get_pipeline_step(db, step_id)
    if not step or step.pipeline_id != pipeline_id:
        raise HTTPException(status_code=404, detail="Pipeline step not found")
    
    # Update step
    try:
        updated_step = await update_pipeline_step(
            db=db,
            step_id=step_id,
            data=step_data.dict(exclude_unset=True)
        )
        return updated_step
    except Exception as e:
        logger.exception("Error updating pipeline step")
        raise HTTPException(status_code=500, detail=f"Failed to update pipeline step: {str(e)}")


@router.delete("/{pipeline_id}/steps/{step_id}", status_code=204)
async def delete_pipeline_step_by_id(
    pipeline_id: str = Path(...),
    step_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a pipeline step.
    
    This endpoint deletes a specific step from a pipeline.
    """
    # Check if pipeline exists
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check ownership
    if pipeline.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this pipeline")
    
    # Check if step exists
    step = await get_pipeline_step(db, step_id)
    if not step or step.pipeline_id != pipeline_id:
        raise HTTPException(status_code=404, detail="Pipeline step not found")
    
    # Delete step
    try:
        success = await delete_pipeline_step(db, step_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete pipeline step")
    except Exception as e:
        logger.exception("Error deleting pipeline step")
        raise HTTPException(status_code=500, detail=f"Failed to delete pipeline step: {str(e)}")


@router.post("/{pipeline_id}/steps/reorder", status_code=200)
async def reorder_pipeline_steps_endpoint(
    step_order: PipelineStepOrderUpdate,
    pipeline_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Reorder steps in a pipeline.
    
    This endpoint updates the order of steps in a pipeline.
    """
    # Check if pipeline exists
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check ownership
    if pipeline.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to modify this pipeline")
    
    # Reorder steps
    try:
        success = await reorder_pipeline_steps(
            db=db,
            pipeline_id=pipeline_id,
            step_order=[(s.step_id, s.order) for s in step_order.steps]
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reorder pipeline steps")
    except Exception as e:
        logger.exception("Error reordering pipeline steps")
        raise HTTPException(status_code=500, detail=f"Failed to reorder pipeline steps: {str(e)}")
    
    # Return updated steps
    steps = await get_pipeline_steps(db, pipeline_id)
    return {"steps": steps}


# --- Pipeline Execution Routes ---

@router.post("/{pipeline_id}/execute", response_model=PipelineExecutionResponse)
async def execute_pipeline_endpoint(
    execute_data: PipelineExecuteRequest,
    pipeline_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Execute a pipeline.
    
    This endpoint starts a pipeline execution with the provided input parameters.
    """
    # Check if pipeline exists
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check access permission
    if pipeline.user_id != current_user.id and not pipeline.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to execute this pipeline")
    
    # Execute pipeline
    try:
        # Use enhanced engine for dry run support
        from pipeline.enhanced_execution_engine import EnhancedPipelineExecutor
        
        engine = EnhancedPipelineExecutor(db)
        result = await engine.execute_pipeline(
            pipeline_id=pipeline_id,
            user_id=current_user.id,
            input_parameters=execute_data.input_parameters or {},
            dry_run=execute_data.dry_run,
            debug_mode=execute_data.debug_mode
        )
        
        # Convert result to response format
        return PipelineExecutionResponse(
            id=result["execution_id"],
            pipeline_id=pipeline_id,
            user_id=current_user.id,
            status=result["status"],
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow() if result["status"] in ["completed", "failed"] else None,
            input_parameters=execute_data.input_parameters,
            results={"final_output": result.get("final_output")},
            error=result.get("error"),
            duration_ms=int(result.get("execution_time", 0) * 1000),
            metadata={
                "total_cost": result.get("total_cost", 0),
                "total_tokens": result.get("total_tokens", 0),
                "dry_run": execute_data.dry_run,
                "step_results": result.get("step_results", [])
            }
        )
    except PipelineExecutionError as e:
        logger.exception("Error executing pipeline")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected error executing pipeline")
        raise HTTPException(status_code=500, detail=f"Failed to execute pipeline: {str(e)}")


@router.get("/executions", response_model=List[PipelineExecutionResponse])
async def list_pipeline_executions(
    pipeline_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    include_step_executions: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List pipeline executions.
    
    This endpoint returns a list of pipeline executions for the current user.
    """
    try:
        executions = await get_pipeline_executions(
            db=db,
            pipeline_id=pipeline_id,
            user_id=current_user.id,
            status=status,
            skip=skip,
            limit=limit,
            include_step_executions=include_step_executions
        )
        return executions
    except Exception as e:
        logger.exception("Error listing pipeline executions")
        raise HTTPException(status_code=500, detail=f"Failed to list pipeline executions: {str(e)}")


@router.get("/executions/{execution_id}", response_model=PipelineExecutionResponse)
async def get_pipeline_execution_by_id(
    execution_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a pipeline execution by ID.
    
    This endpoint returns a specific pipeline execution with all its step executions.
    """
    from db.pipeline_crud import get_pipeline_execution
    
    # Get execution
    execution = await get_pipeline_execution(db, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Pipeline execution not found")
    
    # Check ownership
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this execution")
    
    return execution


@router.post("/{pipeline_id}/execute-enhanced", response_model=Dict[str, Any])
async def execute_pipeline_enhanced(
    execute_data: PipelineExecuteRequest,
    pipeline_id: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Execute a pipeline using the enhanced provider-based execution engine.
    
    This endpoint uses the new provider abstraction layer for improved
    AI model support and cost tracking.
    """
    # Check if pipeline exists
    pipeline = await get_pipeline(db, pipeline_id)
    if not pipeline:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Check access permission
    if pipeline.user_id != current_user.id and not pipeline.is_public:
        raise HTTPException(status_code=403, detail="Not authorized to execute this pipeline")
    
    # Execute pipeline using enhanced executor
    try:
        executor = EnhancedPipelineExecutor(db)
        result = await executor.execute_pipeline(
            pipeline_id=pipeline_id,
            user_id=current_user.id,
            input_parameters=execute_data.input_parameters or {}
        )
        return result
    except Exception as e:
        logger.exception("Error executing pipeline with enhanced executor")
        raise HTTPException(status_code=500, detail=f"Failed to execute pipeline: {str(e)}")


# --- Provider Management Routes ---

@router.get("/providers", response_model=Dict[str, Any])
async def list_available_providers(
    current_user: User = Depends(get_current_user)
):
    """
    List all available AI providers and their capabilities.
    """
    try:
        from providers.registry import get_registry
        registry = get_registry()
        
        providers = registry.list_registered_providers()
        
        return {
            "providers": providers,
            "total": len(providers)
        }
    except Exception as e:
        logger.exception("Error listing providers")
        raise HTTPException(status_code=500, detail=f"Failed to list providers: {str(e)}")


@router.post("/providers/{provider_type}/test", response_model=Dict[str, Any])
async def test_provider_credentials(
    provider_type: str = Path(...),
    credentials: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user)
):
    """
    Test provider credentials by performing a health check.
    """
    try:
        from providers import ProviderType, ProviderCredentials
        from providers.registry import get_registry
        
        # Create credentials object
        provider_creds = ProviderCredentials(
            provider_type=ProviderType(provider_type),
            api_key=credentials.get("api_key"),
            organization_id=credentials.get("organization_id"),
            project_id=credentials.get("project_id"),
            endpoint=credentials.get("endpoint")
        )
        
        # Test the provider
        registry = get_registry()
        async with registry.get_provider_context(ProviderType(provider_type), provider_creds) as provider:
            status = await provider.health_check()
            
            return {
                "provider": provider_type,
                "status": "healthy" if status.is_available else "unhealthy",
                "response_time": status.response_time,
                "error_rate": status.error_rate,
                "last_check": status.last_check.isoformat()
            }
            
    except Exception as e:
        logger.exception(f"Error testing provider {provider_type}")
        return {
            "provider": provider_type,
            "status": "error",
            "error": str(e)
        }


@router.get("/providers/{provider_type}/models", response_model=List[Dict[str, Any]])
async def get_provider_models(
    provider_type: str = Path(...),
    current_user: User = Depends(get_current_user)
):
    """
    Get available models from a specific provider.
    """
    try:
        from providers import ProviderType, ProviderCredentials
        from providers.registry import get_registry
        
        # Get user's credentials for this provider
        from db import crud
        from utils.encryption import decrypt_provider_credentials
        
        user_settings = await crud.get_user_settings(db, current_user.id)
        
        if not user_settings or not user_settings.provider_credentials:
            raise HTTPException(status_code=400, detail=f"No credentials configured for {provider_type}")
        
        provider_creds_data = user_settings.provider_credentials.get(provider_type)
        if not provider_creds_data:
            raise HTTPException(status_code=400, detail=f"No credentials configured for {provider_type}")
        
        # Decrypt credentials
        try:
            decrypted_creds = decrypt_provider_credentials(
                provider_creds_data.get("encrypted_api_key", ""),
                provider_creds_data.get("encrypted_data")
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to decrypt credentials: {str(e)}")
        
        # Create credentials object
        provider_creds = ProviderCredentials(
            provider_type=ProviderType(provider_type),
            api_key=decrypted_creds.get("api_key"),
            organization_id=decrypted_creds.get("organization_id"),
            project_id=decrypted_creds.get("project_id"),
            endpoint=decrypted_creds.get("endpoint")
        )
        
        # Get models
        registry = get_registry()
        async with registry.get_provider_context(ProviderType(provider_type), provider_creds) as provider:
            models = await provider.get_available_models()
            
            return [
                {
                    "id": model.id,
                    "name": model.name,
                    "capabilities": [cap.value for cap in model.capabilities],
                    "context_window": model.context_window,
                    "max_output_tokens": model.max_output_tokens,
                    "input_cost_per_1k": model.input_cost_per_1k,
                    "output_cost_per_1k": model.output_cost_per_1k,
                    "supports_streaming": model.supports_streaming,
                    "supports_functions": model.supports_functions,
                    "supports_vision": model.supports_vision
                }
                for model in models
            ]
            
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting models for provider {provider_type}")
        raise HTTPException(status_code=500, detail=f"Failed to get models: {str(e)}")


# --- Cost Tracking Routes ---

@router.get("/cost-tracking/usage", response_model=Dict[str, Any])
async def get_usage_metrics(
    provider: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user)
):
    """
    Get usage metrics and cost tracking information.
    """
    try:
        from providers.cost_tracker_db import get_cost_tracker
        from providers.types import ProviderType
        from datetime import datetime, timedelta
        
        cost_tracker = get_cost_tracker(db)
        
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()
        
        provider_filter = ProviderType(provider) if provider else None
        
        metrics = await cost_tracker.get_usage_metrics(
            provider=provider_filter,
            start_date=start_date,
            end_date=end_date,
            user_id=current_user.id
        )
        
        daily_costs = await cost_tracker.get_daily_costs(days=days, user_id=current_user.id)
        
        return {
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": days
            },
            "metrics": {
                "total_requests": metrics.total_requests,
                "total_tokens": metrics.total_tokens,
                "total_cost": metrics.total_cost,
                "average_cost_per_request": metrics.average_cost_per_request,
                "average_tokens_per_request": metrics.average_tokens_per_request,
                "models_used": metrics.models_used,
                "operations": metrics.operations,
                "cost_by_model": metrics.cost_by_model,
                "cost_by_operation": metrics.cost_by_operation
            },
            "daily_breakdown": daily_costs
        }
        
    except Exception as e:
        logger.exception("Error getting usage metrics")
        raise HTTPException(status_code=500, detail=f"Failed to get usage metrics: {str(e)}")


# --- Provider Credential Management Routes ---

@router.post("/providers/{provider_type}/credentials", response_model=Dict[str, Any])
async def save_provider_credentials(
    provider_type: str = Path(...),
    credentials: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Save encrypted provider credentials for the current user.
    """
    try:
        from utils.encryption import encrypt_provider_credentials, validate_credentials
        from db.crud import update_user_provider_credentials
        
        # Validate credentials format
        is_valid, error_message = validate_credentials(provider_type, credentials)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_message)
        
        # Encrypt credentials
        encrypted = encrypt_provider_credentials(provider_type, credentials)
        
        # Save to database
        success = await update_user_provider_credentials(
            db=db,
            user_id=current_user.id,
            provider_type=provider_type,
            credentials=encrypted
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to save credentials")
        
        return {
            "message": f"Credentials for {provider_type} saved successfully",
            "provider_type": provider_type
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error saving credentials for {provider_type}")
        raise HTTPException(status_code=500, detail=f"Failed to save credentials: {str(e)}")


@router.delete("/providers/{provider_type}/credentials")
async def delete_provider_credentials(
    provider_type: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete provider credentials for the current user.
    """
    try:
        from db.crud import update_user_provider_credentials, get_user_settings
        
        # Get current settings
        settings = await get_user_settings(db, current_user.id)
        if settings and settings.provider_credentials:
            provider_creds = settings.provider_credentials.copy()
            if provider_type in provider_creds:
                del provider_creds[provider_type]
                
                # Update settings
                await update_user_provider_credentials(
                    db=db,
                    user_id=current_user.id,
                    provider_type=provider_type,
                    credentials={}
                )
        
        return {"message": f"Credentials for {provider_type} deleted successfully"}
        
    except Exception as e:
        logger.exception(f"Error deleting credentials for {provider_type}")
        raise HTTPException(status_code=500, detail=f"Failed to delete credentials: {str(e)}")


@router.get("/providers/{provider_type}/credentials/status", response_model=Dict[str, Any])
async def check_provider_credentials_status(
    provider_type: str = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if credentials are configured for a provider (without revealing them).
    """
    try:
        from db.crud import get_user_settings
        
        settings = await get_user_settings(db, current_user.id)
        
        has_credentials = False
        if settings and settings.provider_credentials:
            provider_creds = settings.provider_credentials.get(provider_type)
            has_credentials = bool(provider_creds and provider_creds.get("encrypted_api_key"))
        
        return {
            "provider_type": provider_type,
            "has_credentials": has_credentials,
            "last_updated": settings.updated_at.isoformat() if settings else None
        }
        
    except Exception as e:
        logger.exception(f"Error checking credentials status for {provider_type}")
        raise HTTPException(status_code=500, detail=f"Failed to check credentials status: {str(e)}")