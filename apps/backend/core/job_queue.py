"""
Background Job Queue System

This module provides a comprehensive job queue system for async processing
using Redis as the backend with fallback to in-memory processing.
"""

import asyncio
import json
import logging
import traceback
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, asdict
import inspect

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class JobResult:
    """Job execution result."""
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    timestamp: Optional[datetime] = None


@dataclass
class Job:
    """Job definition with metadata."""
    id: str
    queue_name: str
    function_name: str
    args: List[Any]
    kwargs: Dict[str, Any]
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3
    retry_count: int = 0
    retry_delay: int = 60  # seconds
    timeout: int = 300  # seconds
    
    # Metadata
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Results
    result: Optional[JobResult] = None
    
    # Context
    user_id: Optional[str] = None
    workspace_id: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'started_at', 'completed_at']:
            if data[field]:
                data[field] = data[field].isoformat()
        
        # Convert enums to values
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        
        # Handle result
        if self.result:
            result_data = asdict(self.result)
            if result_data.get('timestamp'):
                result_data['timestamp'] = result_data['timestamp'].isoformat()
            data['result'] = result_data
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary."""
        # Convert datetime fields
        for field in ['created_at', 'started_at', 'completed_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        
        # Convert enums
        data['priority'] = JobPriority(data['priority'])
        data['status'] = JobStatus(data['status'])
        
        # Handle result
        if data.get('result'):
            result_data = data['result']
            if result_data.get('timestamp'):
                result_data['timestamp'] = datetime.fromisoformat(result_data['timestamp'])
            data['result'] = JobResult(**result_data)
        
        return cls(**data)


class JobQueue:
    """Base class for job queue implementations."""
    
    async def enqueue(self, job: Job) -> str:
        """Add job to queue."""
        raise NotImplementedError
    
    async def dequeue(self, queue_name: str) -> Optional[Job]:
        """Get next job from queue."""
        raise NotImplementedError
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        raise NotImplementedError
    
    async def update_job(self, job: Job) -> bool:
        """Update job status and metadata."""
        raise NotImplementedError
    
    async def get_queue_size(self, queue_name: str) -> int:
        """Get number of jobs in queue."""
        raise NotImplementedError
    
    async def get_jobs(self, queue_name: str = None, status: JobStatus = None, limit: int = 100) -> List[Job]:
        """Get jobs with filtering."""
        raise NotImplementedError


class RedisJobQueue(JobQueue):
    """Redis-based job queue implementation."""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/1"):
        self.redis_url = redis_url
        self.redis_client = None
        
    async def connect(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            await self.redis_client.ping()
            logger.info("Redis job queue connected successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Redis job queue: {e}")
            return False
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def enqueue(self, job: Job) -> str:
        """Add job to Redis queue."""
        if not self.redis_client:
            raise RuntimeError("Redis client not connected")
        
        # Store job data
        job_key = f"job:{job.id}"
        queue_key = f"queue:{job.queue_name}"
        
        job_data = json.dumps(job.to_dict(), default=str)
        
        # Use transaction for atomicity
        pipe = self.redis_client.pipeline()
        pipe.hset(job_key, "data", job_data)
        pipe.zadd(queue_key, {job.id: job.priority.value})
        await pipe.execute()
        
        logger.debug(f"Enqueued job {job.id} to queue {job.queue_name}")
        return job.id
    
    async def dequeue(self, queue_name: str) -> Optional[Job]:
        """Get highest priority job from queue."""
        if not self.redis_client:
            return None
        
        queue_key = f"queue:{queue_name}"
        
        # Get highest priority job (ZREVRANGE gets highest scores first)
        jobs = await self.redis_client.zrevrange(queue_key, 0, 0)
        if not jobs:
            return None
        
        job_id = jobs[0]
        
        # Remove from queue and get job data
        pipe = self.redis_client.pipeline()
        pipe.zrem(queue_key, job_id)
        pipe.hget(f"job:{job_id}", "data")
        results = await pipe.execute()
        
        job_data = results[1]
        if not job_data:
            return None
        
        return Job.from_dict(json.loads(job_data))
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        if not self.redis_client:
            return None
        
        job_data = await self.redis_client.hget(f"job:{job_id}", "data")
        if not job_data:
            return None
        
        return Job.from_dict(json.loads(job_data))
    
    async def update_job(self, job: Job) -> bool:
        """Update job in Redis."""
        if not self.redis_client:
            return False
        
        job_key = f"job:{job.id}"
        job_data = json.dumps(job.to_dict(), default=str)
        
        await self.redis_client.hset(job_key, "data", job_data)
        return True
    
    async def get_queue_size(self, queue_name: str) -> int:
        """Get queue size."""
        if not self.redis_client:
            return 0
        
        return await self.redis_client.zcard(f"queue:{queue_name}")
    
    async def get_jobs(self, queue_name: str = None, status: JobStatus = None, limit: int = 100) -> List[Job]:
        """Get jobs with filtering."""
        if not self.redis_client:
            return []
        
        jobs = []
        
        # Get all job keys
        job_keys = await self.redis_client.keys("job:*")
        
        for job_key in job_keys[:limit]:
            job_data = await self.redis_client.hget(job_key, "data")
            if job_data:
                job = Job.from_dict(json.loads(job_data))
                
                # Apply filters
                if queue_name and job.queue_name != queue_name:
                    continue
                if status and job.status != status:
                    continue
                
                jobs.append(job)
        
        return jobs


class MemoryJobQueue(JobQueue):
    """In-memory job queue implementation for development."""
    
    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.queues: Dict[str, List[str]] = {}  # queue_name -> [job_ids]
        self._lock = asyncio.Lock()
    
    async def enqueue(self, job: Job) -> str:
        """Add job to memory queue."""
        async with self._lock:
            self.jobs[job.id] = job
            
            if job.queue_name not in self.queues:
                self.queues[job.queue_name] = []
            
            self.queues[job.queue_name].append(job.id)
            # Sort by priority (highest first)
            self.queues[job.queue_name].sort(
                key=lambda jid: self.jobs[jid].priority.value,
                reverse=True
            )
        
        return job.id
    
    async def dequeue(self, queue_name: str) -> Optional[Job]:
        """Get next job from memory queue."""
        async with self._lock:
            if queue_name not in self.queues or not self.queues[queue_name]:
                return None
            
            job_id = self.queues[queue_name].pop(0)
            return self.jobs.get(job_id)
    
    async def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        return self.jobs.get(job_id)
    
    async def update_job(self, job: Job) -> bool:
        """Update job in memory."""
        if job.id in self.jobs:
            self.jobs[job.id] = job
            return True
        return False
    
    async def get_queue_size(self, queue_name: str) -> int:
        """Get queue size."""
        return len(self.queues.get(queue_name, []))
    
    async def get_jobs(self, queue_name: str = None, status: JobStatus = None, limit: int = 100) -> List[Job]:
        """Get jobs with filtering."""
        jobs = []
        
        for job in self.jobs.values():
            if queue_name and job.queue_name != queue_name:
                continue
            if status and job.status != status:
                continue
            
            jobs.append(job)
            
            if len(jobs) >= limit:
                break
        
        return jobs


class JobWorker:
    """Job worker that processes jobs from the queue."""
    
    def __init__(self, job_queue: JobQueue, queue_name: str):
        self.job_queue = job_queue
        self.queue_name = queue_name
        self.running = False
        self.functions: Dict[str, Callable] = {}
        
    def register_function(self, name: str, func: Callable):
        """Register a function that can be called by jobs."""
        self.functions[name] = func
        logger.info(f"Registered job function: {name}")
    
    async def start(self):
        """Start the worker."""
        self.running = True
        logger.info(f"Starting job worker for queue: {self.queue_name}")
        
        while self.running:
            try:
                job = await self.job_queue.dequeue(self.queue_name)
                if job:
                    await self._process_job(job)
                else:
                    # No jobs available, wait before checking again
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Worker error: {e}")
                await asyncio.sleep(5)  # Back off on error
    
    async def stop(self):
        """Stop the worker."""
        self.running = False
        logger.info(f"Stopping job worker for queue: {self.queue_name}")
    
    async def _process_job(self, job: Job):
        """Process a single job."""
        logger.info(f"Processing job {job.id}: {job.function_name}")
        
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        await self.job_queue.update_job(job)
        
        start_time = datetime.utcnow()
        
        try:
            # Get function
            if job.function_name not in self.functions:
                raise ValueError(f"Function {job.function_name} not registered")
            
            func = self.functions[job.function_name]
            
            # Execute function with timeout
            if inspect.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*job.args, **job.kwargs),
                    timeout=job.timeout
                )
            else:
                # Run sync function in thread pool
                result = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: func(*job.args, **job.kwargs)
                )
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update job with success
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = JobResult(
                success=True,
                result=result,
                execution_time=execution_time,
                timestamp=datetime.utcnow()
            )
            
            logger.info(f"Job {job.id} completed successfully in {execution_time:.2f}s")
            
        except asyncio.TimeoutError:
            await self._handle_job_failure(job, "Job timed out", start_time)
        except Exception as e:
            await self._handle_job_failure(job, str(e), start_time)
        
        # Update job in queue
        await self.job_queue.update_job(job)
    
    async def _handle_job_failure(self, job: Job, error: str, start_time: datetime):
        """Handle job failure with retry logic."""
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.error(f"Job {job.id} failed: {error}")
        
        job.retry_count += 1
        
        if job.retry_count <= job.max_retries:
            # Schedule retry
            job.status = JobStatus.RETRY
            logger.info(f"Scheduling retry {job.retry_count}/{job.max_retries} for job {job.id}")
            
            # Add delay for retry (exponential backoff)
            retry_delay = job.retry_delay * (2 ** (job.retry_count - 1))
            await asyncio.sleep(min(retry_delay, 300))  # Cap at 5 minutes
            
            # Re-enqueue the job
            job.status = JobStatus.PENDING
            await self.job_queue.enqueue(job)
        else:
            # Mark as failed
            job.status = JobStatus.FAILED
            job.completed_at = datetime.utcnow()
            job.result = JobResult(
                success=False,
                error=error,
                execution_time=execution_time,
                timestamp=datetime.utcnow()
            )


class JobManager:
    """Main job manager that coordinates job queues and workers."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url
        self.job_queue = None
        self.workers: Dict[str, JobWorker] = {}
        self.worker_tasks: Dict[str, asyncio.Task] = {}
        
    async def initialize(self):
        """Initialize the job queue backend."""
        # Try Redis first
        if REDIS_AVAILABLE and self.redis_url:
            redis_queue = RedisJobQueue(self.redis_url)
            if await redis_queue.connect():
                self.job_queue = redis_queue
                logger.info("Using Redis job queue")
                return
        
        # Fallback to memory queue
        self.job_queue = MemoryJobQueue()
        logger.info("Using memory job queue")
    
    async def shutdown(self):
        """Shutdown job manager and all workers."""
        # Stop all workers
        for worker in self.workers.values():
            await worker.stop()
        
        # Cancel worker tasks
        for task in self.worker_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.worker_tasks:
            await asyncio.gather(*self.worker_tasks.values(), return_exceptions=True)
        
        # Close job queue
        if hasattr(self.job_queue, 'disconnect'):
            await self.job_queue.disconnect()
    
    def create_worker(self, queue_name: str) -> JobWorker:
        """Create a worker for a specific queue."""
        if queue_name in self.workers:
            return self.workers[queue_name]
        
        worker = JobWorker(self.job_queue, queue_name)
        self.workers[queue_name] = worker
        return worker
    
    async def start_worker(self, queue_name: str):
        """Start a worker for a queue."""
        if queue_name not in self.workers:
            self.create_worker(queue_name)
        
        if queue_name not in self.worker_tasks:
            worker = self.workers[queue_name]
            task = asyncio.create_task(worker.start())
            self.worker_tasks[queue_name] = task
            logger.info(f"Started worker for queue: {queue_name}")
    
    async def enqueue_job(
        self,
        queue_name: str,
        function_name: str,
        *args,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        timeout: int = 300,
        user_id: str = None,
        workspace_id: str = None,
        **kwargs
    ) -> str:
        """Enqueue a new job."""
        job = Job(
            id=str(uuid.uuid4()),
            queue_name=queue_name,
            function_name=function_name,
            args=list(args),
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            timeout=timeout,
            user_id=user_id,
            workspace_id=workspace_id
        )
        
        await self.job_queue.enqueue(job)
        logger.info(f"Enqueued job {job.id} for function {function_name}")
        return job.id
    
    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and results."""
        job = await self.job_queue.get_job(job_id)
        if not job:
            return None
        
        return {
            "id": job.id,
            "status": job.status.value,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "retry_count": job.retry_count,
            "result": job.result.to_dict() if job.result else None
        }
    
    async def get_queue_stats(self, queue_name: str) -> Dict[str, Any]:
        """Get queue statistics."""
        total_jobs = len(await self.job_queue.get_jobs(queue_name=queue_name))
        pending_jobs = len(await self.job_queue.get_jobs(queue_name=queue_name, status=JobStatus.PENDING))
        running_jobs = len(await self.job_queue.get_jobs(queue_name=queue_name, status=JobStatus.RUNNING))
        completed_jobs = len(await self.job_queue.get_jobs(queue_name=queue_name, status=JobStatus.COMPLETED))
        failed_jobs = len(await self.job_queue.get_jobs(queue_name=queue_name, status=JobStatus.FAILED))
        
        return {
            "queue_name": queue_name,
            "total_jobs": total_jobs,
            "pending": pending_jobs,
            "running": running_jobs,
            "completed": completed_jobs,
            "failed": failed_jobs,
            "worker_active": queue_name in self.worker_tasks
        }


# Global job manager instance
job_manager = JobManager()


# Common job queues
class JobQueues:
    DEFAULT = "default"
    EMAIL = "email"
    ANALYTICS = "analytics"
    BACKUP = "backup"
    CLEANUP = "cleanup"
    AI_PROCESSING = "ai_processing"
    FILE_PROCESSING = "file_processing"