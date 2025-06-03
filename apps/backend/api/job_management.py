"""
Job Queue Management API

Provides endpoints for managing background jobs and monitoring job queue performance.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

from db.database import get_db
from db.crud import user_has_permission
from auth.jwt import get_current_user
from auth.schemas import UserResponse
from core.job_queue import job_manager, JobPriority, JobStatus, JobQueues

router = APIRouter(prefix="/api/jobs", tags=["Job Management"])


class JobRequest(BaseModel):
    """Job creation request model."""
    queue_name: str
    function_name: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    priority: str = "normal"  # low, normal, high, urgent
    max_retries: int = 3
    timeout: int = 300


class JobResponse(BaseModel):
    """Job response model."""
    id: str
    queue_name: str
    function_name: str
    status: str
    priority: str
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    retry_count: int
    result: Optional[Dict[str, Any]]


class QueueStats(BaseModel):
    """Queue statistics model."""
    queue_name: str
    total_jobs: int
    pending: int
    running: int
    completed: int
    failed: int
    worker_active: bool


def _priority_from_string(priority_str: str) -> JobPriority:
    """Convert string to JobPriority enum."""
    mapping = {
        "low": JobPriority.LOW,
        "normal": JobPriority.NORMAL,
        "high": JobPriority.HIGH,
        "urgent": JobPriority.URGENT
    }
    return mapping.get(priority_str.lower(), JobPriority.NORMAL)


@router.post("/enqueue", response_model=Dict[str, str])
async def enqueue_job(
    job_request: JobRequest,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Enqueue a new background job."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "jobs.create")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Validate queue name
    valid_queues = [
        JobQueues.DEFAULT,
        JobQueues.EMAIL,
        JobQueues.ANALYTICS,
        JobQueues.BACKUP,
        JobQueues.CLEANUP,
        JobQueues.AI_PROCESSING,
        JobQueues.FILE_PROCESSING
    ]
    
    if job_request.queue_name not in valid_queues:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid queue name. Valid queues: {valid_queues}"
        )
    
    try:
        job_id = await job_manager.enqueue_job(
            queue_name=job_request.queue_name,
            function_name=job_request.function_name,
            *job_request.args,
            priority=_priority_from_string(job_request.priority),
            max_retries=job_request.max_retries,
            timeout=job_request.timeout,
            user_id=current_user.id,
            **job_request.kwargs
        )
        
        return {"job_id": job_id, "message": "Job enqueued successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to enqueue job: {str(e)}")


@router.get("/status/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get job status and results."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "jobs.read")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    job_status = await job_manager.get_job_status(job_id)
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status


@router.get("/queue/{queue_name}/stats", response_model=QueueStats)
async def get_queue_stats(
    queue_name: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for a specific queue."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "jobs.read")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        stats = await job_manager.get_queue_stats(queue_name)
        return QueueStats(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get queue stats: {str(e)}")


@router.get("/queues/overview")
async def get_all_queues_overview(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get overview of all job queues."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "jobs.read")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    queues = [
        JobQueues.DEFAULT,
        JobQueues.EMAIL,
        JobQueues.ANALYTICS,
        JobQueues.BACKUP,
        JobQueues.CLEANUP,
        JobQueues.AI_PROCESSING,
        JobQueues.FILE_PROCESSING
    ]
    
    overview = []
    for queue_name in queues:
        try:
            stats = await job_manager.get_queue_stats(queue_name)
            overview.append(stats)
        except Exception as e:
            overview.append({
                "queue_name": queue_name,
                "error": str(e),
                "total_jobs": 0,
                "pending": 0,
                "running": 0,
                "completed": 0,
                "failed": 0,
                "worker_active": False
            })
    
    return {"queues": overview}


@router.post("/workers/{queue_name}/start")
async def start_worker(
    queue_name: str,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a worker for a specific queue."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "jobs.manage")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        await job_manager.start_worker(queue_name)
        return {"message": f"Worker started for queue: {queue_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start worker: {str(e)}")


@router.get("/workers/status")
async def get_workers_status(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get status of all workers."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "jobs.read")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    workers_status = []
    for queue_name, worker in job_manager.workers.items():
        workers_status.append({
            "queue_name": queue_name,
            "running": worker.running,
            "task_active": queue_name in job_manager.worker_tasks,
            "registered_functions": list(worker.functions.keys())
        })
    
    return {"workers": workers_status}


@router.get("/jobs")
async def list_jobs(
    queue_name: Optional[str] = Query(None, description="Filter by queue name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(50, ge=1, le=500, description="Number of jobs to return"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List jobs with optional filtering."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "jobs.read")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Convert status string to enum if provided
        status_enum = None
        if status:
            try:
                status_enum = JobStatus(status.lower())
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        jobs = await job_manager.job_queue.get_jobs(
            queue_name=queue_name,
            status=status_enum,
            limit=limit
        )
        
        # Convert jobs to response format
        job_responses = []
        for job in jobs:
            job_responses.append({
                "id": job.id,
                "queue_name": job.queue_name,
                "function_name": job.function_name,
                "status": job.status.value,
                "priority": job.priority.name.lower(),
                "created_at": job.created_at.isoformat() if job.created_at else None,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "retry_count": job.retry_count,
                "result": job.result.to_dict() if job.result else None
            })
        
        return {"jobs": job_responses, "total": len(job_responses)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")


@router.post("/test-job")
async def create_test_job(
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a test job for demonstration purposes."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "jobs.create")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Register a simple test function
        worker = job_manager.create_worker(JobQueues.DEFAULT)
        
        async def test_function(name: str, duration: int = 5):
            """Test function that simulates work."""
            import asyncio
            await asyncio.sleep(duration)
            return f"Hello {name}! Task completed after {duration} seconds."
        
        worker.register_function("test_function", test_function)
        
        # Start worker if not already running
        if JobQueues.DEFAULT not in job_manager.worker_tasks:
            await job_manager.start_worker(JobQueues.DEFAULT)
        
        # Enqueue test job
        job_id = await job_manager.enqueue_job(
            queue_name=JobQueues.DEFAULT,
            function_name="test_function",
            "World",  # positional argument for name parameter
            priority=JobPriority.NORMAL,
            user_id=current_user.id,
            duration=3  # keyword argument passed via **kwargs
        )
        
        return {"job_id": job_id, "message": "Test job created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create test job: {str(e)}")


@router.post("/analytics/generate-report")
async def generate_analytics_report(
    report_type: str = Query(..., description="Type of report to generate"),
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Generate an analytics report as a background job."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "analytics.read")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Register analytics function if not already registered
        worker = job_manager.create_worker(JobQueues.ANALYTICS)
        
        async def generate_analytics_report(report_type: str, user_id: str):
            """Generate analytics report function."""
            import asyncio
            
            # Simulate report generation
            await asyncio.sleep(10)  # Simulated processing time
            
            return {
                "report_type": report_type,
                "generated_by": user_id,
                "generated_at": datetime.utcnow().isoformat(),
                "data": f"Sample {report_type} report data",
                "metrics": {
                    "total_users": 150,
                    "active_workspaces": 25,
                    "total_conversations": 500
                }
            }
        
        worker.register_function("generate_analytics_report", generate_analytics_report)
        
        # Start worker if not already running
        if JobQueues.ANALYTICS not in job_manager.worker_tasks:
            await job_manager.start_worker(JobQueues.ANALYTICS)
        
        # Enqueue analytics job
        job_id = await job_manager.enqueue_job(
            queue_name=JobQueues.ANALYTICS,
            function_name="generate_analytics_report",
            report_type,  # positional argument
            current_user.id,  # positional argument
            priority=JobPriority.NORMAL,
            timeout=600,  # 10 minutes
            user_id=current_user.id
        )
        
        return {"job_id": job_id, "message": f"Analytics report generation started for: {report_type}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics report: {str(e)}")


@router.get("/health")
async def job_queue_health(
    current_user: UserResponse = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Check job queue system health."""
    # Check permission
    has_permission = await user_has_permission(db, current_user.id, "system.monitor")
    if not has_permission:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        # Check if job manager is initialized
        if not job_manager.job_queue:
            return {"status": "unhealthy", "error": "Job queue not initialized"}
        
        # Test basic operations
        test_stats = await job_manager.get_queue_stats(JobQueues.DEFAULT)
        
        # Check worker status
        active_workers = len([w for w in job_manager.workers.values() if w.running])
        total_workers = len(job_manager.workers)
        
        return {
            "status": "healthy",
            "backend_type": type(job_manager.job_queue).__name__,
            "active_workers": active_workers,
            "total_workers": total_workers,
            "test_queue_stats": test_stats
        }
        
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}