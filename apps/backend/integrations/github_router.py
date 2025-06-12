"""
GitHub Integration API Router

Provides endpoints for GitHub integration functionality including
pipeline synchronization, version control, and collaboration features.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from db.database import get_db
from auth.jwt import get_current_active_user
from db.models import User
from db import crud
from integrations.github import GitHubIntegration, GitHubConfig, GitHubCommit
from utils.encryption import encrypt_provider_credentials as encrypt_credentials, decrypt_provider_credentials as decrypt_credentials

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/github",
    tags=["github"],
    responses={404: {"description": "Not found"}},
)


# Request/Response schemas
from pydantic import BaseModel, Field


class GitHubSetupRequest(BaseModel):
    """Request to set up GitHub integration."""
    token: str = Field(..., description="GitHub personal access token")
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    branch: str = Field(default="main", description="Default branch")
    pipelines_path: str = Field(default="pipelines", description="Path for pipelines")


class GitHubStatusResponse(BaseModel):
    """GitHub integration status response."""
    connected: bool
    repository: Optional[Dict[str, Any]] = None
    config: Optional[Dict[str, str]] = None


class PipelineSyncRequest(BaseModel):
    """Request to sync a pipeline with GitHub."""
    pipeline_id: str
    commit_message: Optional[str] = None
    create_pr: bool = False
    pr_title: Optional[str] = None
    pr_body: Optional[str] = None


class PipelineImportRequest(BaseModel):
    """Request to import a pipeline from GitHub."""
    pipeline_id: str
    branch: Optional[str] = None
    overwrite: bool = False


# Helper functions
async def get_github_integration(
    user: User,
    db: AsyncSession
) -> Optional[GitHubIntegration]:
    """Get GitHub integration for a user."""
    try:
        # Get user settings
        user_settings = await crud.get_user_settings(db, user.id)
        if not user_settings or not user_settings.github_config:
            return None
        
        # Decrypt GitHub config
        decrypted_config = decrypt_credentials(user_settings.github_config)
        config = GitHubConfig(**decrypted_config)
        
        return GitHubIntegration(config)
    except Exception as e:
        logger.error(f"Failed to get GitHub integration: {e}")
        return None


# Endpoints
@router.post("/setup")
async def setup_github_integration(
    setup_data: GitHubSetupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Set up GitHub integration for the current user."""
    try:
        # Test connection
        config = GitHubConfig(
            token=setup_data.token,
            owner=setup_data.owner,
            repo=setup_data.repo,
            branch=setup_data.branch,
            pipelines_path=setup_data.pipelines_path
        )
        
        github = GitHubIntegration(config)
        if not await github.test_connection():
            raise HTTPException(status_code=401, detail="Invalid GitHub credentials")
        
        # Verify repository access
        repo = await github.get_repository()
        if not repo:
            raise HTTPException(
                status_code=404, 
                detail=f"Repository {setup_data.owner}/{setup_data.repo} not found or not accessible"
            )
        
        # Save encrypted config to user settings
        encrypted_config = encrypt_credentials(setup_data.dict())
        
        user_settings = await crud.get_user_settings(db, current_user.id)
        if user_settings:
            await crud.update_user_settings(
                db,
                current_user.id,
                github_config=encrypted_config
            )
        else:
            await crud.create_user_settings(
                db,
                user_id=current_user.id,
                github_config=encrypted_config
            )
        
        return {
            "message": "GitHub integration configured successfully",
            "repository": {
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo["description"],
                "url": repo["html_url"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to setup GitHub integration")
        raise HTTPException(status_code=500, detail=f"Failed to setup GitHub integration: {str(e)}")


@router.get("/status", response_model=GitHubStatusResponse)
async def get_github_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get GitHub integration status."""
    try:
        github = await get_github_integration(current_user, db)
        if not github:
            return GitHubStatusResponse(connected=False)
        
        # Test connection
        connected = await github.test_connection()
        if not connected:
            return GitHubStatusResponse(connected=False)
        
        # Get repository info
        repo = await github.get_repository()
        
        return GitHubStatusResponse(
            connected=True,
            repository=repo,
            config={
                "owner": github.config.owner,
                "repo": github.config.repo,
                "branch": github.config.branch,
                "pipelines_path": github.config.pipelines_path
            }
        )
        
    except Exception as e:
        logger.exception("Failed to get GitHub status")
        return GitHubStatusResponse(connected=False)


@router.post("/disconnect")
async def disconnect_github(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Disconnect GitHub integration."""
    try:
        user_settings = await crud.get_user_settings(db, current_user.id)
        if user_settings:
            await crud.update_user_settings(
                db,
                current_user.id,
                github_config=None
            )
        
        return {"message": "GitHub integration disconnected"}
        
    except Exception as e:
        logger.exception("Failed to disconnect GitHub")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect GitHub: {str(e)}")


@router.post("/sync/pipeline")
async def sync_pipeline_to_github(
    sync_data: PipelineSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Sync a pipeline to GitHub."""
    try:
        github = await get_github_integration(current_user, db)
        if not github:
            raise HTTPException(status_code=400, detail="GitHub integration not configured")
        
        # Get pipeline
        pipeline = await crud.get_pipeline(db, sync_data.pipeline_id)
        if not pipeline:
            raise HTTPException(status_code=404, detail="Pipeline not found")
        
        # Check ownership
        if pipeline.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to sync this pipeline")
        
        # Get pipeline steps
        steps = await crud.get_pipeline_steps(db, sync_data.pipeline_id)
        
        # Prepare pipeline data
        pipeline_data = {
            "id": pipeline.id,
            "name": pipeline.name,
            "description": pipeline.description,
            "version": pipeline.version,
            "tags": pipeline.tags,
            "config": pipeline.config,
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "type": step.type,
                    "order": step.order,
                    "config": step.config,
                    "description": step.description,
                    "input_mapping": step.input_mapping,
                    "output_mapping": step.output_mapping,
                    "is_enabled": step.is_enabled,
                    "timeout": step.timeout,
                    "retry_config": step.retry_config
                }
                for step in steps
            ],
            "created_at": pipeline.created_at.isoformat(),
            "updated_at": pipeline.updated_at.isoformat() if pipeline.updated_at else None
        }
        
        # Create PR if requested
        if sync_data.create_pr:
            # Create a new branch
            branch_name = f"pipeline-update-{pipeline.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            if not await github.create_branch(branch_name):
                raise HTTPException(status_code=500, detail="Failed to create branch")
            
            # Save to the new branch
            success = await github.save_pipeline(
                pipeline_id=pipeline.id,
                pipeline_data=pipeline_data,
                message=sync_data.commit_message or f"Update pipeline: {pipeline.name}"
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to save pipeline to GitHub")
            
            # Create pull request
            pr = await github.create_pull_request(
                title=sync_data.pr_title or f"Update pipeline: {pipeline.name}",
                body=sync_data.pr_body or f"Updates to pipeline {pipeline.name}",
                head_branch=branch_name
            )
            
            if not pr:
                raise HTTPException(status_code=500, detail="Failed to create pull request")
            
            return {
                "message": "Pipeline synced and pull request created",
                "pull_request": {
                    "number": pr["number"],
                    "url": pr["html_url"],
                    "title": pr["title"]
                }
            }
        else:
            # Direct commit to default branch
            success = await github.save_pipeline(
                pipeline_id=pipeline.id,
                pipeline_data=pipeline_data,
                message=sync_data.commit_message or f"Update pipeline: {pipeline.name}"
            )
            
            if not success:
                raise HTTPException(status_code=500, detail="Failed to save pipeline to GitHub")
            
            return {"message": "Pipeline synced successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to sync pipeline to GitHub")
        raise HTTPException(status_code=500, detail=f"Failed to sync pipeline: {str(e)}")


@router.post("/import/pipeline")
async def import_pipeline_from_github(
    import_data: PipelineImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Import a pipeline from GitHub."""
    try:
        github = await get_github_integration(current_user, db)
        if not github:
            raise HTTPException(status_code=400, detail="GitHub integration not configured")
        
        # Load pipeline from GitHub
        pipeline_data = await github.load_pipeline(
            pipeline_id=import_data.pipeline_id,
            branch=import_data.branch
        )
        
        if not pipeline_data:
            raise HTTPException(status_code=404, detail="Pipeline not found in GitHub repository")
        
        # Check if pipeline already exists
        existing_pipeline = await crud.get_pipeline(db, import_data.pipeline_id)
        
        if existing_pipeline and not import_data.overwrite:
            raise HTTPException(
                status_code=409, 
                detail="Pipeline already exists. Set overwrite=true to replace it."
            )
        
        # Import or update pipeline
        if existing_pipeline:
            # Update existing pipeline
            await crud.update_pipeline(
                db,
                pipeline_id=import_data.pipeline_id,
                name=pipeline_data.get("name"),
                description=pipeline_data.get("description"),
                tags=pipeline_data.get("tags"),
                config=pipeline_data.get("config"),
                version=pipeline_data.get("version")
            )
            
            # Update steps
            # First, delete existing steps
            existing_steps = await crud.get_pipeline_steps(db, import_data.pipeline_id)
            for step in existing_steps:
                await crud.delete_pipeline_step(db, step.id)
            
            # Create new steps
            for step_data in pipeline_data.get("steps", []):
                await crud.create_pipeline_step(
                    db,
                    pipeline_id=import_data.pipeline_id,
                    name=step_data["name"],
                    step_type=step_data["type"],
                    order=step_data["order"],
                    config=step_data["config"],
                    description=step_data.get("description"),
                    input_mapping=step_data.get("input_mapping"),
                    output_mapping=step_data.get("output_mapping"),
                    is_enabled=step_data.get("is_enabled", True),
                    timeout=step_data.get("timeout"),
                    retry_config=step_data.get("retry_config")
                )
            
            return {"message": "Pipeline updated from GitHub"}
        else:
            # Create new pipeline
            new_pipeline = await crud.create_pipeline(
                db,
                user_id=current_user.id,
                name=pipeline_data["name"],
                description=pipeline_data.get("description"),
                tags=pipeline_data.get("tags"),
                config=pipeline_data.get("config")
            )
            
            # Create steps
            for step_data in pipeline_data.get("steps", []):
                await crud.create_pipeline_step(
                    db,
                    pipeline_id=new_pipeline.id,
                    name=step_data["name"],
                    step_type=step_data["type"],
                    order=step_data["order"],
                    config=step_data["config"],
                    description=step_data.get("description"),
                    input_mapping=step_data.get("input_mapping"),
                    output_mapping=step_data.get("output_mapping"),
                    is_enabled=step_data.get("is_enabled", True),
                    timeout=step_data.get("timeout"),
                    retry_config=step_data.get("retry_config")
                )
            
            return {
                "message": "Pipeline imported from GitHub",
                "pipeline_id": new_pipeline.id
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to import pipeline from GitHub")
        raise HTTPException(status_code=500, detail=f"Failed to import pipeline: {str(e)}")


@router.get("/pipelines")
async def list_github_pipelines(
    branch: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List pipelines in GitHub repository."""
    try:
        github = await get_github_integration(current_user, db)
        if not github:
            raise HTTPException(status_code=400, detail="GitHub integration not configured")
        
        pipelines = await github.list_pipelines(branch)
        
        return {"pipelines": pipelines}
        
    except Exception as e:
        logger.exception("Failed to list GitHub pipelines")
        raise HTTPException(status_code=500, detail=f"Failed to list pipelines: {str(e)}")


@router.get("/pipelines/{pipeline_id}/history")
async def get_pipeline_history(
    pipeline_id: str,
    limit: int = Query(10, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get commit history for a pipeline."""
    try:
        github = await get_github_integration(current_user, db)
        if not github:
            raise HTTPException(status_code=400, detail="GitHub integration not configured")
        
        history = await github.get_pipeline_history(pipeline_id, limit)
        
        return {
            "pipeline_id": pipeline_id,
            "history": [
                {
                    "sha": commit.sha,
                    "message": commit.message,
                    "author": commit.author,
                    "date": commit.date
                }
                for commit in history
            ]
        }
        
    except Exception as e:
        logger.exception("Failed to get pipeline history")
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")